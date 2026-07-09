"""Streamlit rendering helpers for the deep agent's intermediate steps.

Kept separate from ``app.py`` so the message-formatting logic (which has
nothing to do with Streamlit widgets/layout) can be unit tested without a
running Streamlit session.
"""

from __future__ import annotations

import streamlit as st

from careerforge.export import markdown_to_docx_bytes, markdown_to_plain_text

STATUS_ICONS = {"pending": "⬜", "in_progress": "🔄", "completed": "✅"}
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def extract_text(content) -> str:
    """AIMessage.content may be a plain string or a list of content blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return str(content)


def render_steps(messages) -> None:
    """Show the agent's intermediate work: tool calls, todos, subagent tasks."""
    for msg in messages:
        msg_type = getattr(msg, "type", "")
        if msg_type == "ai" and getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                name, args = tc["name"], tc["args"]
                if name == "write_todos":
                    with st.expander("📋 Planning — write_todos", expanded=False):
                        for todo in args.get("todos", []):
                            icon = STATUS_ICONS.get(todo.get("status"), "⬜")
                            st.markdown(f"{icon} {todo.get('content', todo)}")
                elif name == "task":
                    with st.expander(
                        f"🤖 Subagent — {args.get('subagent_type', 'task')}",
                        expanded=False,
                    ):
                        st.markdown(args.get("description", ""))
                elif name == "internet_search":
                    with st.expander(
                        f"🔎 Web search — “{args.get('query', '')}”", expanded=False
                    ):
                        st.json(args)
                elif name in ("write_file", "edit_file", "read_file", "ls", "glob", "grep"):
                    label = args.get("file_path") or args.get("path") or ""
                    with st.expander(f"📁 File system — {name} {label}", expanded=False):
                        st.json(args)
                else:
                    with st.expander(f"🛠️ Tool — {name}", expanded=False):
                        st.json(args)
        elif msg_type == "tool":
            text = extract_text(msg.content)
            if len(text) > 700:
                text = text[:700] + " ...(truncated)"
            with st.expander(f"↩️ Result — {getattr(msg, 'name', 'tool')}", expanded=False):
                st.code(text)


def file_label(path: str) -> str:
    """Short, readable tab label for a virtual file path, e.g.
    '/jobs/acme-eng/resume.md' -> 'acme-eng/resume.md'."""
    parts = [p for p in path.split("/") if p]
    return "/".join(parts[-2:]) if len(parts) > 1 else (parts[0] if parts else path)


def render_files(files: dict) -> None:
    """Render each generated document as properly formatted markdown (not a
    raw code block), with a download button, one tab per file."""
    if not files:
        return
    st.markdown(f"#### 🗂️ Generated documents ({len(files)})")
    items = list(files.items())
    tabs = st.tabs([file_label(path) for path, _ in items]) if len(items) > 1 else None
    for i, (path, data) in enumerate(items):
        content = data.get("content", "") if isinstance(data, dict) else str(data)
        container = tabs[i] if tabs else st.container()
        with container:
            base_name = path.lstrip("/").replace("/", "_").rsplit(".", 1)[0]
            dl_md, dl_txt, dl_docx = st.columns(3)
            dl_md.download_button(
                "⬇️ Markdown (.md)", content,
                file_name=f"{base_name}.md", key=f"dl-md-{path}",
            )
            dl_txt.download_button(
                "⬇️ Plain text (.txt)", markdown_to_plain_text(content),
                file_name=f"{base_name}.txt", key=f"dl-txt-{path}",
            )
            dl_docx.download_button(
                "⬇️ Word (.docx)", markdown_to_docx_bytes(content),
                file_name=f"{base_name}.docx", mime=DOCX_MIME, key=f"dl-docx-{path}",
            )
            st.markdown(content or "*(empty file)*")
