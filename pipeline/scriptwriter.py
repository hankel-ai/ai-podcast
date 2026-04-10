import logging
import os
import re
from datetime import datetime

from sources.base import Story

logger = logging.getLogger(__name__)

TRANSITIONS = [
    "Next up.",
    "In other news.",
    "Also making headlines.",
    "Moving on to our next story.",
    "And now.",
    "Turning our attention to.",
    "Here's another interesting one.",
    "Meanwhile.",
    "On a related note.",
    "Also worth noting.",
]

# Acronyms that TTS should spell out
ACRONYMS = {
    "LLM": "L.L.M.",
    "LLMs": "L.L.M.s",
    "GPT": "G.P.T.",
    "API": "A.P.I.",
    "APIs": "A.P.I.s",
    "GPU": "G.P.U.",
    "GPUs": "G.P.U.s",
    "TPU": "T.P.U.",
    "CPU": "C.P.U.",
    "RAG": "R.A.G.",
    "NLP": "N.L.P.",
    "MLOps": "M.L.Ops",
    "RLHF": "R.L.H.F.",
    "CUDA": "CUDA",
    "SDK": "S.D.K.",
    "CLI": "C.L.I.",
}


def generate_script(stories: list[Story], config: dict) -> str:
    mode = config.get("podcast", {}).get("script_mode", "template")
    conversation = config.get("podcast", {}).get("conversation", False)

    if mode == "ollama":
        return _generate_ollama_script(stories, config, conversation)
    elif mode == "ai":
        return _generate_ai_script(stories, config, conversation)
    else:
        return _generate_template_script(stories, config, conversation)


def _generate_template_script(stories: list[Story], config: dict, conversation: bool = False) -> str:
    title = config.get("podcast", {}).get("title", "AI Daily Briefing")
    date_str = datetime.now().strftime("%A, %B %d, %Y")

    if conversation:
        return _generate_template_conversation(stories, title, date_str)

    parts = []

    # Intro
    parts.append(
        f"Good morning! This is your {title} for {date_str}. "
        f"Here are today's top {len(stories)} stories from the world of artificial intelligence."
    )
    parts.append('<break time="1s"/>')

    # Stories
    for i, story in enumerate(stories):
        if i > 0:
            transition = TRANSITIONS[i % len(TRANSITIONS)]
            parts.append(f'<break time="800ms"/>{transition}')

        segment = f"Story number {_number_word(i + 1)}. From {story.source_name}. {story.title}."
        if story.summary:
            # Trim summary to ~2 sentences
            summary = _trim_to_sentences(story.summary, max_sentences=2)
            segment += f" {summary}"
        parts.append(segment)

    # Links callout
    parts.append('<break time="1s"/>')
    parts.append(
        "Links to all the stories mentioned today are in the message below this audio. "
        "Check them out for the full details."
    )

    # Outro
    parts.append('<break time="800ms"/>')
    parts.append(f"That wraps up today's {title}. Stay curious, and I'll see you tomorrow.")

    script = "\n\n".join(parts)
    return _cleanup_for_tts(script)


COHOST_REACTIONS = [
    "Oh that's interesting.",
    "That's a big deal.",
    "I've been following this one.",
    "Wow, really?",
    "That makes sense actually.",
    "I saw that trending yesterday.",
    "That's significant.",
    "Hmm, that's worth watching.",
]


def _generate_template_conversation(stories: list[Story], title: str, date_str: str) -> str:
    parts = []

    parts.append(f"HOST: Good morning everyone! Welcome to your {title} for {date_str}. We've got {len(stories)} stories to cover today.")
    parts.append(f"COHOST: Morning! Yeah, it's been a busy day in the AI world. Let's get into it.")

    for i, story in enumerate(stories):
        reaction = COHOST_REACTIONS[i % len(COHOST_REACTIONS)]
        parts.append(f"HOST: Story number {_number_word(i + 1)}, from {story.source_name}. {story.title}.")
        if story.summary:
            summary = _trim_to_sentences(story.summary, max_sentences=2)
            parts.append(f"HOST: {summary}")
        parts.append(f"COHOST: {reaction}")

    parts.append(f"HOST: That's all for today's {title}. Links to everything are in the message below.")
    parts.append("COHOST: Definitely check those out. See you all tomorrow!")

    script = "\n\n".join(parts)
    return _cleanup_for_tts(script)


def _format_stories_for_prompt(stories: list[Story]) -> str:
    story_list = []
    for i, story in enumerate(stories, 1):
        entry = f"{i}. [{story.source_name}] {story.title}"
        if story.summary:
            entry += f"\n   Summary: {story.summary}"
        if story.article_content:
            # Trim to ~500 chars per story to keep prompt manageable
            content = story.article_content[:500]
            entry += f"\n   Article excerpt: {content}"
        story_list.append(entry)
    return "\n\n".join(story_list)


def _build_prompt(stories: list[Story], config: dict) -> str:
    title = config.get("podcast", {}).get("title", "AI Daily Briefing")
    date_str = datetime.now().strftime("%A, %B %d, %Y")
    stories_text = _format_stories_for_prompt(stories)

    return f"""Write a podcast script for "{title}" dated {date_str}.

Here are today's AI news stories:

{stories_text}

Requirements:
- Write a 5-7 minute spoken script (about 800-1000 words)
- Start with a brief, energetic greeting and date
- Cover each story with a natural summary and brief commentary on why it matters
- Use the article excerpts to provide specific details, numbers, and quotes — don't just paraphrase headlines
- Draw connections between related stories when possible
- Especially highlight anything about agentic coding, new model releases, or open-source AI
- Use conversational tone — this is spoken audio, not written text
- End with a brief sign-off mentioning that links are in the message below
- Do NOT include any stage directions, speaker labels, or non-spoken text
- Do NOT use markdown formatting
- Output ONLY the spoken words"""


def _build_conversation_prompt(stories: list[Story], config: dict) -> str:
    title = config.get("podcast", {}).get("title", "AI Daily Briefing")
    date_str = datetime.now().strftime("%A, %B %d, %Y")
    stories_text = _format_stories_for_prompt(stories)

    return f"""Write a two-host podcast script for "{title}" dated {date_str}.

The hosts are:
- HOST: The main presenter who introduces stories and provides context
- COHOST: A knowledgeable co-host who reacts, asks questions, adds perspective, and sometimes plays devil's advocate

Here are today's AI news stories:

{stories_text}

Requirements:
- Write a 7-10 minute conversational script (about 1000-1400 words)
- Format each line as either HOST: or COHOST: followed by their dialogue
- HOST opens with a greeting and date, COHOST responds naturally
- For each story: HOST introduces it, COHOST reacts or adds insight, they briefly discuss
- Use the article excerpts to provide specific details, numbers, and quotes — not just headline summaries
- The conversation should feel natural — interruptions, agreement, surprise, humor are all good
- Draw connections between related stories when possible
- Especially highlight anything about agentic coding, new model releases, or open-source AI
- HOST wraps up with a sign-off, COHOST adds a final thought
- Mention that links are in the message below
- Do NOT include stage directions like (laughs), [pause], etc.
- Do NOT use markdown formatting
- Every line MUST start with either "HOST:" or "COHOST:"
- Output ONLY the spoken dialogue"""


def _generate_ollama_script(stories: list[Story], config: dict, conversation: bool = False) -> str:
    import httpx

    ollama_config = config.get("ollama", {})
    base_url = ollama_config.get("url", "http://localhost:11434")
    model = ollama_config.get("model", "llama3")

    prompt = _build_conversation_prompt(stories, config) if conversation else _build_prompt(stories, config)

    try:
        resp = httpx.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=300,
        )
        resp.raise_for_status()
        script = resp.json().get("response", "")
        if script.strip():
            logger.info(f"Ollama script generated with model={model}")
            return _cleanup_for_tts(script)
        else:
            logger.warning("Ollama returned empty response, falling back to template mode")
            return _generate_template_script(stories, config, conversation)
    except Exception as e:
        logger.warning(f"Ollama failed ({e}), falling back to template mode")
        return _generate_template_script(stories, config, conversation)


def _get_anthropic_client():
    """Return an Anthropic client, preferring Vertex AI if configured."""
    import anthropic

    vertex_project = os.environ.get("ANTHROPIC_VERTEX_PROJECT_ID")
    if vertex_project:
        region = os.environ.get("CLOUD_ML_REGION", "us-east5")
        logger.info(f"Using Vertex AI (project={vertex_project}, region={region})")
        return anthropic.AnthropicVertex(project_id=vertex_project, region=region), True

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        logger.info("Using Anthropic API key")
        return anthropic.Anthropic(api_key=api_key), False

    return None, False


def _generate_ai_script(stories: list[Story], config: dict, conversation: bool = False) -> str:
    try:
        import anthropic  # noqa: F401
    except ImportError:
        logger.warning("anthropic package not installed, falling back to template mode")
        return _generate_template_script(stories, config, conversation)

    client, is_vertex = _get_anthropic_client()
    if not client:
        logger.warning("No Anthropic credentials found (set ANTHROPIC_VERTEX_PROJECT_ID or ANTHROPIC_API_KEY), falling back to template mode")
        return _generate_template_script(stories, config, conversation)

    # Vertex AI uses @ as version separator, Anthropic API uses -
    model = "claude-haiku-4-5@20251001" if is_vertex else "claude-haiku-4-5-20251001"

    prompt = _build_conversation_prompt(stories, config) if conversation else _build_prompt(stories, config)

    message = client.messages.create(
        model=model,
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )

    script = message.content[0].text
    return _cleanup_for_tts(script)


def _cleanup_for_tts(text: str) -> str:
    # Expand acronyms
    for acronym, expansion in ACRONYMS.items():
        text = re.sub(r'\b' + re.escape(acronym) + r'\b', expansion, text)

    # Replace special characters
    text = text.replace("&", " and ")
    text = text.replace("@", " at ")
    text = text.replace("#", " number ")
    text = text.replace("$", " dollars ")

    # Remove URLs from spoken text
    text = re.sub(r'https?://\S+', '', text)

    # Replace Unicode arrows and special chars
    text = text.replace("\u2192", " to ")
    text = text.replace("\u2190", " from ")
    text = text.replace("\u2014", ", ")
    text = text.replace("\u2013", " to ")
    text = text.replace("\u2018", "'")
    text = text.replace("\u2019", "'")
    text = text.replace("\u201c", '"')
    text = text.replace("\u201d", '"')

    # Remove markdown
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)

    # Clean up whitespace
    text = re.sub(r'  +', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def _trim_to_sentences(text: str, max_sentences: int = 2) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return " ".join(sentences[:max_sentences])


def _number_word(n: int) -> str:
    words = [
        "one", "two", "three", "four", "five", "six",
        "seven", "eight", "nine", "ten", "eleven", "twelve",
        "thirteen", "fourteen", "fifteen",
    ]
    if 1 <= n <= len(words):
        return words[n - 1]
    return str(n)
