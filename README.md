# Turn.io Google Search

A Python based demo context integration for Turn.io
that returns suggested replies for display in the UI
based on web search results from [Duck Duck Go](https://www.duckduckgo.com).

This can be run as a serverless function.

It also can be used as a webhooks endpoint, where it replies
with search results based on the text of the inbound message.

Remember to set the `TOKEN` environment variable for the replies via Turn to work.
