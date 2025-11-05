# Quick Setup with Ollama (Free Local LLM)

Get started with Answer Sheet Marker in 10 minutes using Ollama - completely free!

## Step 1: Install Ollama (2 minutes)

### macOS
```bash
brew install ollama
```

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows
Download from: https://ollama.com/download

---

## Step 2: Start Ollama & Download Model (5 minutes)

```bash
# Terminal 1: Start Ollama service
ollama serve

# Terminal 2: Download a model
# Option A: Best quality (40GB, requires 64GB RAM)
ollama pull llama3:70b

# Option B: Good balance (4.7GB, requires 8GB RAM) - RECOMMENDED
ollama pull llama3

# Option C: Fastest (4.1GB, requires 8GB RAM)
ollama pull mistral
```

---

## Step 3: Configure Answer Sheet Marker (1 minute)

```bash
# Copy Ollama configuration
cp .env.ollama.example .env

# Edit .env and set your model
# LLM_MODEL=llama3  (or llama3:70b, or mistral)
```

---

## Step 4: Run Your First Marking (2 minutes)

```bash
# Install dependencies if you haven't
poetry install

# Mark answer sheets
poetry run answer-marker mark \
  -g path/to/marking_guide.pdf \
  -a path/to/answer_sheets/ \
  -o ./output
```

---

## Complete Example

```bash
# 1. Install Ollama
brew install ollama

# 2. Start Ollama (keep this terminal open)
ollama serve

# 3. In a new terminal, download model
ollama pull llama3

# 4. Setup Answer Sheet Marker
cd answer-sheet-marker
cp .env.ollama.example .env

# 5. Run marking
poetry run answer-marker mark \
  -g example/Assessment.pdf \
  -a example/ \
  -o example/reports

# Done! Check example/reports/ for results
```

---

## Troubleshooting

### "Could not connect to Ollama"
**Solution**: Make sure `ollama serve` is running in another terminal

### "Model not found"
**Solution**: Download the model first with `ollama pull llama3`

### Out of memory
**Solution**: Use a smaller model:
```bash
ollama pull mistral  # Only 4.1GB
```

### Slow processing
**Solution**: This is normal for local LLMs. Options:
1. Use a smaller model (mistral)
2. Add more RAM
3. Use GPU acceleration if available
4. Process fewer students at once (set BATCH_SIZE=1 in .env)

---

## Performance Tips

### Speed vs Quality

| Model | Size | RAM | Speed | Quality |
|-------|------|-----|-------|---------|
| llama3:70b | 40GB | 64GB+ | Slow | Best |
| llama3 | 4.7GB | 8GB+ | Medium | Good |
| mistral | 4.1GB | 8GB+ | Fast | Good |
| phi3:medium | 7.9GB | 16GB+ | Fast | Good |

### Optimize Performance

1. **Close other applications** to free up RAM
2. **Process in smaller batches**: Set `BATCH_SIZE=1` in `.env`
3. **Use quantized models**: `ollama pull llama3:q4_0` (smaller, faster)
4. **Monitor resources**: `ollama ps` to see running models

---

## Switching to API-Based Service Later

If you need faster processing or better quality, you can easily switch to Anthropic or OpenAI:

```bash
# Just update your .env file
LLM_PROVIDER=anthropic  # or openai, or together
LLM_MODEL=claude-sonnet-4-5-20250929
LLM_API_KEY=your-api-key-here
```

No code changes needed!

---

## Cost Comparison

### Local (Ollama)
- **Setup cost**: $0
- **Per student**: $0
- **Monthly**: $0
- **Hardware**: Need good RAM

### Cloud (Anthropic/OpenAI)
- **Setup cost**: $0
- **Per student**: $0.10-0.50
- **For 100 students**: $10-50/month
- **Hardware**: None needed

Choose based on your needs:
- **Privacy-sensitive?** → Use Ollama
- **High volume?** → Use Ollama
- **Need best quality?** → Use Anthropic
- **Need speed?** → Use Anthropic/OpenAI

---

## Next Steps

1. ✅ Test with your sample assessments
2. ✅ Review the detailed [LLM Configuration Guide](LLM_CONFIGURATION.md)
3. ✅ Check the [main README](../README.md) for full features
4. ✅ Explore other Ollama models: https://ollama.com/library
