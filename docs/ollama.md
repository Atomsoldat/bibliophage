
## GPU Configuration

Ollama is configured to use the host's NVIDIA GPU. If no GPU is available, it will fall back to CPU (with significantly reduced performance).

## Volume Persistence

Models are stored in the `bibliophage-ollama-models` volume, which persists across container recreations.

## API Endpoints

- Base URL: `http://localhost:11435`
- List models: `GET /api/tags`
- Generate: `POST /api/generate`
- Chat: `POST /api/chat`

See [Ollama API documentation](https://github.com/ollama/ollama/blob/main/docs/api.md) for full details.

## Usage Examples

### List Models
```bash
curl http://localhost:11435/api/tags
```

### Generate Completion
```bash
curl http://localhost:11435/api/generate -d '{
  "model": "mistral",
  "prompt": "Explain quantum computing in simple terms",
  "stream": false
}'
```

### Chat Completion
```bash
curl http://localhost:11435/api/chat -d '{
  "model": "mistral",
  "messages": [
    {"role": "user", "content": "What is RAG in AI?"}
  ],
  "stream": false
}'
```

### Python Usage
```python
import ollama

response = ollama.chat(
    model='mistral',
    messages=[
        {'role': 'user', 'content': 'Summarize this document...'}
    ]
)
print(response['message']['content'])
```
