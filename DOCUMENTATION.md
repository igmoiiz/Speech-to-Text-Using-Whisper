# 📖 Jarvis: Comprehensive Technical Documentation

## 1. Executive Summary
Jarvis is an advanced **Agentic Voice AI** framework designed for low-latency, privacy-centric interaction. Unlike traditional "State Machine" assistants, Jarvis leverages a **Non-Deterministic Reasoning Loop** powered by Large Language Models (LLMs). This allows the system to handle underspecified requests, recover from tool failures, and maintain a consistent persona across different modalities.

---

## 2. Structural Architecture

### 2.1 Sensory Layer (`core/`)
The sensory layer is responsible for translating the physical world into data structures and vice-versa.
- **`stt.py` (Whisper Integration)**: Utilizes a standalone `Whisper` instance. It supports `FP16` inference on CUDA-enabled devices, significantly reducing latency.
- **`tts.py` (Neural Synthesis)**: Employs a streaming producer-consumer model. As the LLM completes a sentence, it is immediately dispatched for synthesis, allowing the audio to begin playing before the full response is even generated.
- **`listen.py` (Acoustic Logic)**: 
    - **VAD**: Uses Gaussian Mixture Models (via `webrtcvad`) to identify human speech signatures.
    - **Clap Detection**: Monitors the root-mean-square (RMS) energy levels to identify sharp transients matching the profile of a double clap.

### 2.2 Cognitive Layer (`agent/`)
The cognitive layer serves as the "Orchestrator."
- **`jarvis.py` (The Agent Loop)**: Implements the **Thought-Action-Observation** pattern. It interprets LLM outputs, identifies tool calls via regex, and reinjects the results into the conversation context.
- **`memory.py` (State Management)**: 
    - **Episodic Memory**: Summarizes conversation "episodes" to maintain context beyond the token window.
    - **Semantic Facts**: A structured RAG (Retrieval-Augmented Generation) system that stores user-specific data in a non-volatile JSON format.
- **`tools.py` (Functional Interface)**: Provides a "Sandboxed" interface for the LLM to interact with the OS. It includes robust error handling to prevent system crashes during malformed command execution.

---

## 3. Detailed Component Interaction

### 3.1 The Agentic Reasoning Loop
When a user provides a prompt, the following sequence occurs:
1.  **Context Augmentation**: The system prompt, tool definitions, and long-term memory are injected into the LLM context.
2.  **Inference**: The LLM determines if it can answer directly or requires a tool.
3.  **Tool Execution**: If a tool is called (e.g., `TOOL: search_web(query="...")`), the `execute_tool` router dispatches the command.
4.  **Feedback Integration**: The tool result is formatted as a "User" message (observation) and sent back to the LLM.
5.  **Final Synthesis**: The LLM provides a natural language summary of the action and result.

### 3.2 Data Analysis Engine
Jarvis includes a sophisticated **Natural Language to Data** interface.
- **Pandas Integration**: Allows users to query CSV/Excel files using descriptive language.
- **Logic**: The `analyze_csv` tool handles row filtering, value lookups (ID-based), and statistical aggregations (mean, sum, max) without requiring the user to write code.

---

## 4. Configuration & Optimization

### 4.1 Model Selection
| Tier | Whisper Model | Ollama Model | Hardware Target |
| :--- | :--- | :--- | :--- |
| **Lightweight** | `base` | `qwen2.5:1.5b` | Low-end CPU / Raspberry Pi |
| **Balanced** | `medium` | `qwen2.5:7b` | Standard Desktop / RTX 3060 |
| **Pro** | `large-v3` | `llama3.1:8b` | High-end Workstation / RTX 4080+ |

### 4.2 Environmental Variables
The system heavily relies on `config.py` for fine-tuning. 
- **`VAD_AGGRESSIVENESS`**: Set to `3` for highly noisy environments.
- **`CLAP_THRESHOLD`**: Adjust between `0.1` and `0.5` depending on microphone gain.

---

## 5. Security & Safety Protocols
- **Local-First**: All LLM processing and transcription occur on the local machine. No voice data or documents are sent to external cloud APIs (except for the Edge-TTS and Search-Web tools).
- **Anti-Hallucination**: The system prompt enforces a "Verify then Speak" policy, requiring the agent to use tool results rather than internal weights for factual data.
- **Depth Limiting**: `MAX_TOOL_CALLS` (default: 5) prevents recursive execution or infinite loops in tool calling.

---

## 6. Maintenance & Support

### 6.1 Known Limitations
- High-latency on systems without dedicated GPUs.
- Web search performance depends on current connectivity and `ddgs` backend availability.

### 6.2 Contact Information
For professional inquiries, licensing, or deep technical support, please contact the lead developer:

*   **Lead Developer**: Moiz Baloch
*   **Email**: [moaiz3110@gmail.com](mailto:moaiz3110@gmail.com)
*   **WhatsApp**: [+92 306 7892235](https://wa.me/923067892235)

---

**© 2026 Moiz Baloch. All Technical Specifications are Proprietary.**
