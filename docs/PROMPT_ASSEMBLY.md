## Prompt Assembly & Context Optimization

This system implements **explicit prompt assembly** to maximize grounding quality in RAG-based decision systems.

Rather than building generic conversational memory, the design prioritizes **retrieved knowledge over chat history**, ensuring that responses remain factual, auditable, and token-efficient.

### Design Principles

- **Stateless by Default**  
  Each request is processed independently. The model has no persistent memory across turns.

- **Instruction Pinning**  
  System and developer instructions are always included and never truncated.

- **Retrieval-First Grounding**  
  Retrieved documents are the sole source of factual grounding and citation.

- **Minimal Conversation Context (Clarification Only)**  
  At most the immediately previous turn may be included as *ephemeral clarification context*.  
  Conversation history is never treated as a knowledge source and is never cited.

- **Token-Aware Budgeting**  
  When token limits are reached, conversation context is dropped before retrieved documents.

---

### Why Minimal Clarification Context Exists

This design is based on a simple but reliable human interaction pattern:

> **Human follow-up queries are almost always semantically relative to the immediately previous exchange.**

Users naturally:
- Use pronouns (“it”, “that”, “those”)
- Omit repeated subjects
- Narrow scope incrementally
- Assume shared context from the last turn

Pure stateless RAG can fail on such follow-ups due to ambiguity, even when retrieval is correct.

Including only the **last turn as clarification context**:
- Resolves ambiguity and scope
- Preserves user intent
- Improves question alignment with retrieved documents

Importantly, this clarification context:
- Does **not** introduce new knowledge
- Is **never** treated as factual grounding
- Exists solely to aid interpretation of the current query

---

### Prompt Assembly Order

1. System Instructions (pinned)
2. Retrieved Documents (RAG context, highest priority)
3. Minimal Clarification Context (previous turn only, optional)
4. Current User Question

This ordering ensures that retrieved knowledge dominates the model’s attention while allowing natural follow-up questions.

---

### Interaction Illustration (Minimal Conversational Context)

The following example illustrates how limited conversation context is used only for clarification, while factual grounding always comes from retrieval.

#### Turn 1 — Initial Question

**User**
```

What is Retrieval-Augmented Generation?

```

**Prompt Assembly**
```

[System Instructions]
[Retrieved Docs: RAG definition, architecture]
[User Question: What is Retrieval-Augmented Generation?]

```

**Assistant**
```

Retrieval-Augmented Generation (RAG) is a technique that combines document retrieval with language generation to produce grounded responses. [1]

```

---

#### Turn 2 — Clarification Follow-up

**User**
```

How is it different from fine-tuning?

```

**Prompt Assembly**
```

[System Instructions]
[Retrieved Docs: RAG vs Fine-tuning comparison]
[Previous Assistant Answer: RAG definition]   (clarification only)
[User Question: How is it different from fine-tuning?]

```

**Assistant**
```

Unlike fine-tuning, which modifies model weights, RAG keeps the base model fixed and injects external knowledge at inference time. [2]

```

---

#### Turn 3 — Token Budget Pressure

**User**
```

Give a real-world enterprise example.

```

**Prompt Assembly**
```

[System Instructions]
[Retrieved Docs: Enterprise RAG use cases]
[User Question: Give a real-world enterprise example.]

```

**Assistant**
```

In enterprise IT operations, RAG is commonly used to retrieve incident runbooks and historical RCA reports to guide troubleshooting. [3]

```

In this scenario:
- Conversation context is dropped under token pressure
- Retrieved documents remain authoritative
- Grounding quality and citation integrity are preserved

---

### Key Design Guarantee

Conversation context is treated as **ephemeral clarification aid only**.  
Retrieved documents always take precedence to preserve grounding quality.
