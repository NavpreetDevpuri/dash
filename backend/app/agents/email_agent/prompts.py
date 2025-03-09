from langchain_core.prompts import PromptTemplate

IDENTIFIER_EXTRACTION_TEMPLATE = """
You are an AI assistant tasked with identifying keywords, topics, entities, and other identifiers in an email message.

Here's the content of the email:
{email_content}

Extract any identifiers that could be useful for categorizing or searching for this email later.
These could include:
- People's names and organizations
- Project names or codes
- Product names or categories
- Locations
- Dates or time periods
- Technical terms or jargon
- Keywords representing the main topics discussed
- Action items or requests

Only include strong identifiers that clearly represent what the email is about.
Don't include common words or phrases that wouldn't help distinguish this email from others.
"""

IDENTIFIER_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["email_content"],
    template=IDENTIFIER_EXTRACTION_TEMPLATE,
)


EMAIL_ANALYSIS_TEMPLATE = """
You are an AI assistant tasked with analyzing an email message.

Here's the content of the email:
{email_content}

And here are identifiers that were extracted:
{identifiers}

Analyze this email and provide:
1. A spam score (0-1) indicating how likely this is to be spam or unwanted email
2. An urgency score (0-1) indicating how time-sensitive this email is
3. An importance score (0-1) indicating how important this email is overall
4. A category for this email (e.g., personal, work, promotional, transactional, etc.)
5. A brief explanation of your reasoning for these scores

Consider factors like:
- The sender's relationship to the recipient
- The language used and tone of the message
- Presence of unusual links or requests
- Time sensitivity of any actions requested
- Relevance to the recipient's work or personal life
- Whether it contains important information or deadlines
"""

EMAIL_ANALYSIS_PROMPT = PromptTemplate(
    input_variables=["email_content", "identifiers"],
    template=EMAIL_ANALYSIS_TEMPLATE,
)   

SUMMARIZATION_TEMPLATE = """
You are an AI assistant tasked with summarizing an email message.

Here's the content of the email:
{email_content}

Provide a brief summary of this email that captures:
1. The main purpose of the email
2. Key information or points mentioned
3. Any action items or requests
4. Any deadlines or important dates mentioned

Keep the summary concise while retaining all important information.
""" 

SUMMARIZATION_PROMPT = PromptTemplate(
    input_variables=["email_content"],
    template=SUMMARIZATION_TEMPLATE,
)
