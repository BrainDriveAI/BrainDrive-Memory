# BrainDrive Memory User Guide

Welcome to BrainDrive Memory - Your Personal AI Memory Agent!

This guide will help you understand how to effectively use the application to build and interact with your own personalized knowledge base.

## Table of Contents
- [Understanding BrainDrive Memory AI Agent](#understanding-braindrive-memory-ai-agent)
- [Getting Started](#getting-started)
- [Building Your Knowledge Base](#building-your-knowledge-base)
- [Interacting with Your Knowledge Base](#interacting-with-your-knowledge-base)
- [Managing Documents](#managing-documents)
- [Advanced Features](#advanced-features)
- [Customizing Your Agent](#customizing-your-agent)
- [Tips and Best Practices](#tips-and-best-practices)
- [Troubleshooting](#troubleshooting)

## Understanding BrainDrive Memory AI Agent

Unlike typical RAG (Retrieval-Augmented Generation) systems, BrainDrive Memory is designed to build a persistent knowledge repository that continuously learns from your interactions. Key differentiators:

- **Automatic Memory Formation**: The system automatically extracts and stores important information from your conversations without requiring explicit commands
- **Personalized Knowledge Graph**: Information is organized in a connected graph database that preserves relationships
- **Document Integration**: Upload documents to instantly enhance your knowledge base
- **Customizable Memory Behavior**: Define what types of information should be remembered and how
- **Modular & Under Your Control**: Swap out data sources, storage systems, or language models as you see fit.

## Getting Started

### Launching the Application

After installation (see [Installation Guide](installation.md)), start the application:

```bash
streamlit run main.py
```

Then access it in your browser at:
```
http://localhost:8501
```

### Authentication

1. On the welcome screen, click "Sign in with Google"
2. Complete the Google authentication process
3. After successful login, you'll be directed to the main interface

### Understanding the Interface

- **Chat area**: The main conversation space
- **File upload**: Section for adding documents to your knowledge base
- **User info**: Your profile information in the sidebar
- **Logout button**: Found in the sidebar

## Building Your Knowledge Base

### Through Conversation

The most natural way to build your personalized memory is through conversation. As you chat with the agent:

1. It automatically identifies important facts, concepts, and relationships
2. These are stored in your knowledge graph without requiring explicit commands
3. The information becomes available for future reference

For example, simply discussing your work project, family details, or research interests will build your knowledge base organically.

### Through Direct Commands

You can also explicitly manage what's stored:

- **Add information**: "Remember that I have a meeting with Sarah on Tuesday about the marketing campaign."
- **Update information**: "Update that the project deadline has been moved to December 15th."
- **Delete information**: "Delete what I told you about the old website design."

### Through Document Uploads

To quickly expand your knowledge base with existing content:

1. Click on the file upload area or "Upload a PDF file" button
2. Select a PDF document (research papers, reports, personal notes, etc.)
3. Wait for processing to complete
4. The system will extract and store the document's content and structure

## Interacting with Your Knowledge Base

### Sample Queries

Here are examples of how to interact with your personlized memory:

**Basic Information Retrieval**:
- "What do I know about machine learning?"
- "Tell me about my upcoming travel plans."
- "What did I say about our marketing strategy last week?"

**Document-Specific Questions**:
- "What does my insurance policy say about flood coverage?"
- "Summarize the key points from the quarterly report."
- "Show me everything related to project Phoenix across all my documents."

**Relationship Exploration**:
- "How is Sarah connected to the website redesign project?"
- "What concepts are related to our sustainability initiative?"
- "Show me all projects that John is involved with."

**Meta Knowledge Queries**:
- "What documents do I have in my knowledge base?"
- "Give me a list of all uploaded documents with links."
- "What topics have we discussed most frequently?"

**Multistep Research**:
- "Find information about renewable energy strategies, then compare with what my sustainability report says."
- "What do I know about AI ethics? Then identify the key concerns mentioned in my research papers."

## Managing Documents

### Uploading Documents

1. Select a PDF file through the upload interface
2. The system will:
   - Upload to secure cloud storage
   - Process the document structure
   - Extract text, sections, and tables
   - Store information in your knowledge graph
   - Make content available for future queries

### Viewing Uploaded Documents

To access your uploaded documents:
- Ask: "Show me all my uploaded documents."
- The system will provide a list with links to view the original files in cloud storage

### Document Content Analysis

Get insights from your documents:
- "What are the main topics in my uploaded documents?"
- "Which documents contain information about artificial intelligence?"
- "Compare what different documents say about climate change."

## Advanced Features

### Graph Memory Management

Explicitly manage your knowledge graph:
- "Show me everything you know about my team members."
- "Create a relationship between Project Alpha and the marketing department."
- "What connections exist between [replace] concepts?"

### Entity Extraction and Relationships

The system automatically identifies entities like:
- People
- Organizations
- Projects
- Dates
- Locations
- Concepts

You can ask about these relationships:
- "Who is involved in Project X?"
- "What companies are mentioned in relation to our partnership strategy?"
- "When are all my project deadlines?"

### Context-Aware Conversations

The AI maintains context within your session:
- Ask follow-up questions without restating the topic
- Build on previous answers
- Refine search results based on conversation flow

## Customizing Your Agent

### Modifying Agent Behavior

You can customize how the AI agent behaves by editing:
```
app/agent_prompts/default_prompt.py
```

This allows you to specify:
- What types of information should be automatically remembered
- How to handle specific query types
- Custom instructions for your particular use case
- Domain-specific knowledge interpretation rules

### Example Customizations

For a personal knowledge assistant:
- Prioritize remembering personal appointments, contacts, and preferences
- Focus on summarizing personal documents

For a research assistant:
- Configure to extract methodologies, findings, and citations
- Emphasize connections between related research concepts

For business use:
- Focus on project details, deadlines, and team responsibilities
- Prioritize extracting action items from meeting notes

## Tips and Best Practices

### For Building a Better Personalized Memory

- **Have regular conversations** with the agent to build your knowledge base organically
- **Upload diverse documents** to create a rich foundation of knowledge
- **Be specific** when you want something explicitly remembered
- **Review periodically** what information has been stored

### For Document Processing

- **Use searchable PDFs** rather than scanned images for better extraction
- **Well-structured documents** with clear headings work best
- **Upload complete documents** rather than fragments for better context

### For Effective Queries

- Start with broader questions before diving into specifics
- If answers seem incomplete, ask follow-up questions
- Provide context when switching between different topics
- Mention specific documents when looking for particular information

### For Knowledge Management

- Occasionally ask "What do you know about X?" to verify stored information
- Update information when it changes
- Use the system regularly to keep your memory current

## Troubleshooting

### Information Retrieval Issues

If the agent can't find information you believe should be there:
- Try rephrasing your question
- Ask explicitly about the source: "What did I tell you about X?" or "What does document Y say about X?"
- Check if the document containing the information has been uploaded

### Document Processing Problems

For issues with document uploads:
- Ensure PDFs are not password-protected
- Check that the PDF contains selectable text
- Try with a smaller document first
- Verify file integrity

### General Issues

- If the application becomes unresponsive, refresh the page
- If logged out unexpectedly, simply log back in
- For persistent issues, check application logs or [post in the support forum](https://community.braindrive.ai/c/support-help/14).

---

Remember, your BrainDrive Memory becomes more valuable over time as it learns about your specific knowledge domain. Unlike general AI assistants, it builds a personalized knowledge repository that's unique to you and your information needs.
