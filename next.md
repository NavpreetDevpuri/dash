@slack I have this slack agent 
- Have tools for external APIs
- Add data to private db when sending messages through consumer
- Have analyser_agent 
- Have consumer agent and consomer
- user facing agent with tools!
- schemas for output types

I also have whatsapp, but it need some updates like consumers

Now I want the similar for the other agents 

## Email agent 
It will also have similar tools, similar consumer behaviour, on sending email i will also forward it to email consumer where it will add to db in consumer_agent for email and ignore in analyser_agent, 

## Dineout restaurant agent 
It will also have similar tools, some extra like booking, cancling tables for number of people, all about dineout!, finding restaurant will be handled bny public db tool 

## Online food ordering agent
It will also have similar tools, but extra tools for ordering, cancling orders, finding dishes or restaurants will be handled by public db tool

## Calender agent
Similar tools, with extra tools like adding events to calender, adding meetings with title and description. with attendees, udating meetings, ..etc 

## memory agent
This will have similar tools, it just remeber thinsg about the user, it creates memory indetifers in db, always try to keep those number of memory identifers as less like pass on all the exiting memory identifiers and ask to adjust or suggest new in a proper output schema and add those in db, 



Now the point is Dineout restaurant agent and Online food ordering agent will also have a predefined output schemas, liek restaurants, dishes, orders, ..etc For now it will add timer of 20 minutes for the dilivery, which is trigger consumer and it will be marked as dilivered! use some pip package for it



Now it comes to main_user_facing_agent @main.py , right now it is just having basic dummy agents and all using graph, but we want to have a create_react_agent that import all those agents we have created and add those as tool in the main agent, how can we add those as tool? simple, we can have a agent_tool factory function that can return function but before tool function in factory function we can initilize those agents and just keep calling using the same thread_id and all! 
This main agent will also have two functions call_llm and run_interactive (it's interactive will still call call_llm for nested tool agents)


