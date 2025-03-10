"""Question answering over a graph."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from langchain.chains.base import Chain
from langchain.chains.llm import LLMChain
from langchain_core.callbacks import CallbackManagerForChainRun
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import BasePromptTemplate
from pydantic import Field
import networkx as nx
from arango.database import StandardDatabase

from langchain_community.chains.graph_qa.prompts import (
    AQL_FIX_PROMPT,
    AQL_GENERATION_PROMPT,
    AQL_QA_PROMPT,
)
from langchain_community.graphs.arangodb_graph import ArangoGraph

from arango.graph import Graph

class ArangoGraphQAChain(Chain):
    """Chain for question-answering against a graph by generating AQL statements.

    *Security note*: Make sure that the database connection uses credentials
        that are narrowly-scoped to only include necessary permissions.
        Failure to do so may result in data corruption or loss, since the calling
        code may attempt commands that would result in deletion, mutation
        of data if appropriately prompted or reading sensitive data if such
        data is present in the database.
        The best way to guard against such negative outcomes is to (as appropriate)
        limit the permissions granted to the credentials used with this tool.

        See https://python.langchain.com/docs/security for more information.
    """

    graph: ArangoGraph = Field(exclude=True)
    aql_generation_chain: LLMChain
    aql_fix_chain: LLMChain
    qa_chain: Optional[LLMChain] = None
    input_key: str = "query"  #: :meta private:
    output_key: str = "result"  #: :meta private:

    # Specifies the maximum number of AQL Query Results to return
    top_k: int = 10

    # Specifies the set of AQL Query Examples that promote few-shot-learning
    aql_examples: str = ""

    # Specify whether to return the AQL Query in the output dictionary
    return_aql_query: bool = False

    # Specify whether to return the AQL JSON Result in the output dictionary
    return_aql_result: bool = False

    # Specify whether to perform QA on the results or return raw results
    perform_qa: bool = True

    # Specify the maximum amount of AQL Generation attempts that should be made
    max_aql_generation_attempts: int = 3

    allow_dangerous_requests: bool = False
    """Forced user opt-in to acknowledge that the chain can make dangerous requests.

    *Security note*: Make sure that the database connection uses credentials
        that are narrowly-scoped to only include necessary permissions.
        Failure to do so may result in data corruption or loss, since the calling
        code may attempt commands that would result in deletion, mutation
        of data if appropriately prompted or reading sensitive data if such
        data is present in the database.
        The best way to guard against such negative outcomes is to (as appropriate)
        limit the permissions granted to the credentials used with this tool.

        See https://python.langchain.com/docs/security for more information.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the chain."""
        super().__init__(**kwargs)
        if self.allow_dangerous_requests is not True:
            raise ValueError(
                "In order to use this chain, you must acknowledge that it can make "
                "dangerous requests by setting `allow_dangerous_requests` to `True`."
                "You must narrowly scope the permissions of the database connection "
                "to only include necessary permissions. Failure to do so may result "
                "in data corruption or loss or reading sensitive data if such data is "
                "present in the database."
                "Only use this chain if you understand the risks and have taken the "
                "necessary precautions. "
                "See https://python.langchain.com/docs/security for more information."
            )
        
        # Ensure either perform_qa or return_aql_result is True
        if not self.perform_qa and not self.return_aql_result:
            raise ValueError(
                "Either perform_qa or return_aql_result must be True. "
                "Set at least one of these parameters to True to ensure "
                "the chain returns meaningful results."
            )

    @property
    def input_keys(self) -> List[str]:
        return [self.input_key]

    @property
    def output_keys(self) -> List[str]:
        return [self.output_key]

    @property
    def _chain_type(self) -> str:
        return "graph_aql_chain"

    @classmethod
    def from_llm(
        cls,
        llm: BaseLanguageModel,
        *,
        qa_prompt: BasePromptTemplate = AQL_QA_PROMPT,
        aql_generation_prompt: BasePromptTemplate = AQL_GENERATION_PROMPT,
        aql_fix_prompt: BasePromptTemplate = AQL_FIX_PROMPT,
        **kwargs: Any,
    ) -> ArangoGraphQAChain:
        """Initialize from LLM."""
        aql_generation_chain = LLMChain(llm=llm, prompt=aql_generation_prompt)
        aql_fix_chain = LLMChain(llm=llm, prompt=aql_fix_prompt)
        
        # Only create qa_chain if perform_qa is True
        qa_chain = None
        if kwargs.get("perform_qa", True):
            qa_chain = LLMChain(llm=llm, prompt=qa_prompt)
        
        return cls(
            qa_chain=qa_chain,
            aql_generation_chain=aql_generation_chain,
            aql_fix_chain=aql_fix_chain,
            **kwargs,
        )

    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        """
        Generate an AQL statement from user input, use it retrieve a response
        from an ArangoDB Database instance, and respond to the user input
        in natural language or return raw results based on configuration.

        Users can modify the following ArangoGraphQAChain Class Variables:

        :var top_k: The maximum number of AQL Query Results to return
        :type top_k: int

        :var aql_examples: A set of AQL Query Examples that are passed to
            the AQL Generation Prompt Template to promote few-shot-learning.
            Defaults to an empty string.
        :type aql_examples: str

        :var return_aql_query: Whether to return the AQL Query in the
            output dictionary. Defaults to False.
        :type return_aql_query: bool

        :var return_aql_result: Whether to return the AQL JSON Result in the
            output dictionary. Defaults to False
        :type return_aql_result: bool
        
        :var perform_qa: Whether to perform QA on the results or return raw results.
            Defaults to True.
        :type perform_qa: bool

        :var max_aql_generation_attempts: The maximum amount of AQL
            Generation attempts to be made prior to raising the last
            AQL Query Execution Error. Defaults to 3.
        :type max_aql_generation_attempts: int
        """
        _run_manager = run_manager or CallbackManagerForChainRun.get_noop_manager()
        callbacks = _run_manager.get_child()
        user_input = inputs[self.input_key]

        #########################
        # Generate AQL Query #
        aql_generation_output = self.aql_generation_chain.run(
            {
                "adb_schema": self.graph_schema,
                "aql_examples": self.aql_examples,
                "user_input": user_input,
            },
            callbacks=callbacks,
        )
        #########################

        aql_query = ""
        aql_error = ""
        aql_result = None
        aql_generation_attempt = 1

        while (
            aql_result is None
            and aql_generation_attempt < self.max_aql_generation_attempts + 1
        ):
            #####################
            # Extract AQL Query #
            pattern = r"```(?i:aql)?(.*?)```"
            matches = re.findall(pattern, aql_generation_output, re.DOTALL)
            if not matches:
                _run_manager.on_text(
                    "Invalid Response: ", end="\n", verbose=self.verbose
                )
                _run_manager.on_text(
                    aql_generation_output, color="red", end="\n", verbose=self.verbose
                )
                raise ValueError(f"Response is Invalid: {aql_generation_output}")

            aql_query = matches[0]
            #####################

            _run_manager.on_text(
                f"AQL Query ({aql_generation_attempt}):", verbose=self.verbose
            )
            _run_manager.on_text(
                aql_query, color="green", end="\n", verbose=self.verbose
            )

            #####################
            # Execute AQL Query #
            from arango import AQLQueryExecuteError

            try:
                aql_result = self.graph.query(aql_query, self.top_k)
            except AQLQueryExecuteError as e:
                aql_error = e.error_message

                _run_manager.on_text(
                    "AQL Query Execution Error: ", end="\n", verbose=self.verbose
                )
                _run_manager.on_text(
                    aql_error, color="yellow", end="\n\n", verbose=self.verbose
                )

                ########################
                # Retry AQL Generation #
                aql_generation_output = self.aql_fix_chain.run(
                    {
                        "adb_schema": self.graph_schema,
                        "aql_query": aql_query,
                        "aql_error": aql_error,
                    },
                    callbacks=callbacks,
                )
                ########################

            #####################

            aql_generation_attempt += 1

        if aql_result is None:
            m = f"""
                Maximum amount of AQL Query Generation attempts reached.
                Unable to execute the AQL Query due to the following error:
                {aql_error}
            """
            raise ValueError(m)

        _run_manager.on_text("AQL Result:", end="\n", verbose=self.verbose)
        _run_manager.on_text(
            str(aql_result), color="green", end="\n", verbose=self.verbose
        )

        result = {}
        
        # Perform QA if requested
        if self.perform_qa and self.qa_chain is not None:
            ########################
            # Interpret AQL Result #
            qa_result = self.qa_chain(
                {
                    "adb_schema": self.graph_schema,
                    "user_input": user_input,
                    "aql_query": aql_query,
                    "aql_result": aql_result,
                },
                callbacks=callbacks,
            )
            ########################
            result[self.output_key] = qa_result[self.qa_chain.output_key]
        else:
            # Return raw results
            result[self.output_key] = aql_result

        # Always include aql_result in the output if return_aql_result is True
        if self.return_aql_result:
            result["aql_result"] = aql_result

        if self.return_aql_query:
            result["aql_query"] = aql_query

        return result


class ArangoNetworkxQAChain(Chain):
    """Chain for question-answering against a graph by using NetworkX algorithms.

    This chain converts an ArangoDB graph to a NetworkX graph and uses NetworkX algorithms
    to answer complex graph analysis queries that are better suited for NetworkX than AQL.

    *Security note*: Make sure that the database connection uses credentials
        that are narrowly-scoped to only include necessary permissions.
        Failure to do so may result in data corruption or loss, since the calling
        code may attempt commands that would result in deletion, mutation
        of data if appropriately prompted or reading sensitive data if such
        data is present in the database.
        The best way to guard against such negative outcomes is to (as appropriate)
        limit the permissions granted to the credentials used with this tool.

        See https://python.langchain.com/docs/security for more information.
    """
    G_adb: nx.DiGraph = Field(exclude=True)
    db: StandardDatabase = Field(exclude=True)
    graph: Graph = Field(exclude=True)
    graph_schema: Optional[Dict[str, Any]] = Field(exclude=True)
    nx_code_generation_chain: LLMChain
    nx_code_fix_chain: LLMChain
    qa_chain: Optional[LLMChain] = None
    input_key: str = "query"  #: :meta private:
    output_key: str = "result"  #: :meta private:

    # Specify whether to return the NetworkX code in the output dictionary
    return_nx_code: bool = False
    
    # Specify whether to return the raw NetworkX result in the output dictionary
    return_nx_result: bool = False
    
    # Specify whether to perform QA on the results or return raw results
    perform_qa: bool = False
    
    # Specify the maximum amount of NetworkX code generation attempts that should be made
    max_nx_generation_attempts: int = 3
    
    # Specify whether to use a cache to avoid converting the graph multiple times
    use_nx_cache: bool = True
    
    # Internal cache for the NetworkX graph
    _nx_graph_cache: Optional[Any] = None

    def __init__(self, **kwargs: Any) -> None:
        """Initialize from kwargs."""
        super().__init__(**kwargs)
        # Import NetworkX only when this class is instantiated

    @property
    def input_keys(self) -> List[str]:
        """Return the input keys."""
        return [self.input_key]

    @property
    def output_keys(self) -> List[str]:
        """Return the output keys."""
        return [self.output_key]

    @property
    def _chain_type(self) -> str:
        """Return the chain type."""
        return "arango_networkx_qa_chain"

    @classmethod
    def from_llm(
        cls,
        llm: BaseLanguageModel,
        *,
        qa_prompt: Optional[BasePromptTemplate] = None,
        nx_code_generation_prompt: Optional[BasePromptTemplate] = None,
        nx_code_fix_prompt: Optional[BasePromptTemplate] = None,
        **kwargs: Any,
    ) -> ArangoNetworkxQAChain:
        """Initialize from LLM."""
        # Default prompts need to be imported here to avoid circular imports
        from app.common.prompts import (
            NETWORKX_QA_PROMPT,
            NETWORKX_GENERATION_PROMPT,
            NETWORKX_FIX_PROMPT,
        )
        
        # Use provided prompts or defaults
        _qa_prompt = qa_prompt or NETWORKX_QA_PROMPT
        _nx_code_generation_prompt = nx_code_generation_prompt or NETWORKX_GENERATION_PROMPT
        _nx_code_fix_prompt = nx_code_fix_prompt or NETWORKX_FIX_PROMPT
        
        nx_code_generation_chain = LLMChain(llm=llm, prompt=_nx_code_generation_prompt)
        nx_code_fix_chain = LLMChain(llm=llm, prompt=_nx_code_fix_prompt)
        
        # Only create qa_chain if perform_qa is True
        qa_chain = None
        if kwargs.get("perform_qa", True):
            qa_chain = LLMChain(llm=llm, prompt=_qa_prompt)
        
        return cls(
            qa_chain=qa_chain,
            nx_code_generation_chain=nx_code_generation_chain,
            nx_code_fix_chain=nx_code_fix_chain,
            **kwargs,
        )

    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        """Execute the chain."""
        _run_manager = run_manager or CallbackManagerForChainRun.get_noop_manager()
        callbacks = _run_manager.get_child()
        
        # Get user input
        user_input = inputs[self.input_key]
        
        # Initialize variables
        nx_code = None
        nx_error = None
        nx_result = None
        
        # Generate and execute NetworkX code
        for attempt in range(self.max_nx_generation_attempts):
            _run_manager.on_text(
                f"\nAttempt {attempt + 1}/{self.max_nx_generation_attempts}: "
                "Generating NetworkX code...",
                verbose=self.verbose,
            )
            
            # Generate NetworkX code
            nx_generation_inputs = {
                "graph_schema": self.graph_schema,
                "user_input": user_input,
            }
            if nx_error:
                nx_generation_inputs["error"] = nx_error
                
            if attempt == 0:
                nx_code_result = self.nx_code_generation_chain(
                    nx_generation_inputs, callbacks=callbacks
                )
                nx_code = nx_code_result[self.nx_code_generation_chain.output_key]
            else:
                # Use fix chain for subsequent attempts
                nx_code_result = self.nx_code_fix_chain(
                    {
                        "graph_schema": self.graph_schema,
                        "user_input": user_input,
                        "code": nx_code,
                        "error": nx_error,
                    },
                    callbacks=callbacks,
                )
                nx_code = nx_code_result[self.nx_code_fix_chain.output_key]
            
            # Clean up the code (remove markdown code blocks if present)
            nx_code_cleaned = re.sub(r"^```python\n|```$", "", nx_code, flags=re.MULTILINE).strip()
            
            _run_manager.on_text("Generated NetworkX code:", end="\n", verbose=self.verbose)
            _run_manager.on_text(
                nx_code_cleaned, color="yellow", end="\n", verbose=self.verbose
            )
            
            # Execute the NetworkX code
            try:
                _run_manager.on_text(
                    "Executing NetworkX code...", end="\n", verbose=self.verbose
                )
                
                # Prepare global variables for execution
                global_vars = {"G_adb": self.G_adb, "nx": nx}
                local_vars = {}
                
                # Execute the code
                exec(nx_code_cleaned, global_vars, local_vars)
                
                # Check if FINAL_RESULT is in the local variables
                if "FINAL_RESULT" not in local_vars:
                    nx_error = "The code did not define FINAL_RESULT variable. Please ensure the code sets this variable with the final answer."
                    _run_manager.on_text(
                        f"Error: {nx_error}", color="red", end="\n", verbose=self.verbose
                    )
                    continue
                
                # Get the result
                nx_result = local_vars["FINAL_RESULT"]
                
                _run_manager.on_text(
                    "NetworkX code executed successfully!", end="\n", verbose=self.verbose
                )
                break
                
            except Exception as e:
                nx_error = str(e)
                _run_manager.on_text(
                    f"Error executing NetworkX code: {nx_error}",
                    color="red",
                    end="\n",
                    verbose=self.verbose,
                )
                # Print the full error stack trace for debugging
                import traceback
                error_stack = traceback.format_exc()
                print(error_stack)
                
                # If this is the last attempt, raise an error
                if attempt == self.max_nx_generation_attempts - 1:
                    m = f"""
                    Could not successfully execute NetworkX code after 
                    {self.max_nx_generation_attempts} attempts. 
                    Last error: {nx_error}
                    """
                    raise ValueError(m)
        
        # Process the result
        result = {}
        
        # Perform QA if requested
        if self.perform_qa and self.qa_chain is not None:
            _run_manager.on_text(
                "Interpreting NetworkX results...", end="\n", verbose=self.verbose
            )
            qa_result = self.qa_chain(
                {
                    "graph_schema": self.graph_schema,
                    "user_input": user_input,
                    "nx_code": nx_code_cleaned,
                    "nx_result": nx_result,
                },
                callbacks=callbacks,
            )
            result[self.output_key] = qa_result[self.qa_chain.output_key]
        else:
            # Return raw results
            result[self.output_key] = nx_result
            
        # Add additional outputs if requested
        if self.return_nx_code:
            result["nx_code"] = nx_code_cleaned
            
        if self.return_nx_result:
            result["nx_result"] = nx_result
            
        return result



