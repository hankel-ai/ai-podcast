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

    if mode == "ai":
        return _generate_ai_script(stories, config)
    else:
        return _generate_template_script(stories, config)


def _generate_template_script(stories: list[Story], config: dict) -> str:
    title = config.get("podcast", {}).get("title", "AI Daily Briefing")
    date_str = datetime.now().strftime("%A, %B %d, %Y")

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


def _generate_ai_script(stories: list[Story], config: dict) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set, falling back to template mode")
        return _generate_template_script(stories, config)

    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic package not installed, falling back to template mode")
        return _generate_template_script(stories, config)

    title = config.get("podcast", {}).get("title", "AI Daily Briefing")
    date_str = datetime.now().strftime("%A, %B %d, %Y")

    # Build story summaries for the prompt
    story_list = []
    for i, story in enumerate(stories, 1):
        entry = f"{i}. [{story.source_name}] {story.title}"
        if story.summary:
            entry += f"\n   Summary: {story.summary}"
        story_list.append(entry)

    stories_text = "\n\n".join(story_list)

    prompt = f"""Write a podcast script for "{title}" dated {date_str}.

Here are today's AI news stories:

{stories_text}

Requirements:
- Write a 5-7 minute spoken script (about 800-1000 words)
- Start with a brief, energetic greeting and date
- Cover each story with a natural summary and brief commentary on why it matters
- Draw connections between related stories when possible
- Especially highlight anything about agentic coding, new model releases, or open-source AI
- Use conversational tone — this is spoken audio, not written text
- End with a brief sign-off mentioning that links are in the message below
- Do NOT include any stage directions, speaker labels, or non-spoken text
- Do NOT use markdown formatting
- Output ONLY the spoken words"""

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
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
