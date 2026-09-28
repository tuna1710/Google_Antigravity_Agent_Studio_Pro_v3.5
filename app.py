#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛸 Google Antigravity Managed Agent Studio Pro (v3.6)
Compatible with Local environment, Docker, Google Colab, and Cloud Run/VPS.
"""

import os
import sys

# Tự động nạp biến môi trường từ file .env nếu có
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# @title
import os
import sys
import json
import uuid
import shutil
import base64
import mimetypes
import requests
import gradio as gr

# Sửa lỗi proxy nếu có trong môi trường sandbox/container
for k in ["no_proxy", "NO_PROXY", "GLOBAL_AGENT_NO_PROXY"]:
    if k in os.environ and ("[::1]" in os.environ[k] or "::1" in os.environ[k]):
        os.environ[k] = "localhost,127.0.0.1"

from google import genai
from google.genai import types

# Tự động lấy Gemini API Key từ Colab Secrets (nếu đã lưu)
colab_api_key = ""
try:
    from google.colab import userdata
    colab_api_key = userdata.get('GEMINI_API_KEY') or ""
except Exception:
    pass

# Cấu hình đường dẫn lưu trữ thông minh (tự động nhận biết Colab hoặc Local)
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
IS_COLAB = os.path.exists("/content")

if IS_COLAB:
    DRIVE_DIR = "/content/drive/MyDrive/AntigravityAgent"
    BACKUP_DIR = DRIVE_DIR if os.path.exists("/content/drive/MyDrive") else "/content"
    COLAB_DOWNLOAD_DIR = "/content"
else:
    BACKUP_DIR = os.path.join(BASE_DIR, "backup")
    COLAB_DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")

os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(COLAB_DOWNLOAD_DIR, exist_ok=True)
BACKUP_FILE = os.path.join(BACKUP_DIR, "agent_sessions_backup.json")

DEFAULT_AGENT = "antigravity-preview-05-2026"
AVAILABLE_AGENTS = [
    "antigravity-preview-05-2026",
    "deep-research-preview-04-2026",
    "deep-research-max-preview-04-2026",
    "deep-research-pro-preview-12-2025",
    "Tùy chỉnh khác..."
]

# --- Kho Kỹ năng Mẫu Chuẩn (Curated Agent Skills) ---
CURATED_SKILLS = {
    "data-analyst-pro": {
        "name": "data-analyst-pro",
        "desc": "Phân tích dữ liệu chuyên sâu, trực quan hóa biểu đồ đẹp mắt và tính toán thống kê.",
        "type": "inline",
        "content": """---
name: data-analyst-pro
description: Phân tích dữ liệu chuyên sâu, trực quan hóa biểu đồ đẹp mắt và tính toán thống kê.
---
# Data Analyst Pro Skill
- Luôn sử dụng pandas, numpy và matplotlib/seaborn để xử lý dữ liệu.
- Khi vẽ biểu đồ, luôn đặt tiêu đề rõ ràng, nhãn trục, hiển thị grid và lưu thành file ảnh PNG độ phân giải cao (dpi=300).
- Luôn in tóm tắt thống kê (mean, median, min, max, missing values)."""
    },
    "web-scraper-expert": {
        "name": "web-scraper-expert",
        "desc": "Thu thập, trích xuất và chuẩn hóa dữ liệu từ các trang web an toàn.",
        "type": "inline",
        "content": """---
name: web-scraper-expert
description: Thu thập, trích xuất và chuẩn hóa dữ liệu từ các trang web an toàn.
---
# Web Scraper Expert Skill
- Sử dụng BeautifulSoup4, requests hoặc curl để crawl dữ liệu.
- Luôn có cơ chế xử lý ngoại lệ, timeout và đặt User-Agent chuẩn.
- Xuất dữ liệu đã xử lý ra định dạng JSON hoặc CSV sạch sẽ trong thư mục hiện tại."""
    },
    "document-slides-maker": {
        "name": "document-slides-maker",
        "desc": "Tạo báo cáo HTML/PDF và Slide thuyết trình chuyên nghiệp.",
        "type": "inline",
        "content": """---
name: document-slides-maker
description: Tạo báo cáo HTML/PDF và Slide thuyết trình chuyên nghiệp.
---
# Document & Slides Maker Skill
- Định dạng báo cáo thành file HTML đẹp mắt sử dụng TailwindCSS hoặc CSS hiện đại.
- Nếu cần tạo PDF, sử dụng weasyprint, reportlab hoặc công cụ dòng lệnh thích hợp.
- Bố cục trang gồm: Trang bìa, Mục lục tóm tắt, Nội dung chính và Kết luận hành động."""
    },
    "systematic-debugger": {
        "name": "systematic-debugger",
        "desc": "Quy trình phát hiện, cô lập và sửa lỗi mã nguồn theo phương pháp khoa học.",
        "type": "inline",
        "content": """---
name: systematic-debugger
description: Quy trình phát hiện, cô lập và sửa lỗi mã nguồn theo phương pháp khoa học.
---
# Systematic Debugger Skill
- 1. Phân tích Stack Trace và nhật ký lỗi (Error logs).
- 2. Tạo một script tái hiện lỗi tối giản (Minimal Reproducible Example).
- 3. Đặt các câu lệnh in hoặc kiểm tra kiểu dữ liệu để định vị nguyên nhân gốc rễ.
- 4. Viết unit test chứng minh lỗi đã được khắc phục hoàn toàn."""
    },
    "security-auditor": {
        "name": "security-auditor",
        "desc": "Rà soát bảo mật mã nguồn, phát hiện API key bị lộ, SQL injection và lỗ hổng logic.",
        "type": "inline",
        "content": """---
name: security-auditor
description: Rà soát bảo mật mã nguồn, phát hiện API key bị lộ, SQL injection và lỗ hổng logic.
---
# Security Auditor Skill
- Quét toàn bộ tệp mã nguồn để tìm API key, secret token hoặc mật khẩu bị hardcode.
- Kiểm tra các hàm thực thi lệnh (eval, exec, subprocess) để phòng tránh Command Injection.
- Đề xuất giải pháp khắc phục chi tiết và phương án mã hóa an toàn."""
    }
}

# --- Class quản lý phiên tương tác với Antigravity Agent, Skills & Tự động phục hồi Sandbox ---
class ManagedAgentSession:
    def __init__(self, api_key: str, agent: str = DEFAULT_AGENT, system_instruction: str = "", skills: dict = None, env_id: str = None):
        self.api_key = api_key
        self.agent = agent
        self.system_instruction = system_instruction.strip() if system_instruction else ""
        self.skills = skills.copy() if skills else {}
        self.client = genai.Client(api_key=api_key)
        self.env_id = env_id.replace("environments/", "").strip() if env_id else None
        self.last_interaction_id = None
        self.step = 0
        self.auto_recreated = False
        self.old_expired_id = None

    def ask(self, prompt, system_instruction: str = None, skills: dict = None, extra_sources: list = None):
        self.step += 1
        self.auto_recreated = False
        self.old_expired_id = None
        kwargs = {"agent": self.agent, "input": prompt}
        sys_inst = system_instruction if system_instruction is not None else self.system_instruction
        if sys_inst and sys_inst.strip():
            kwargs["system_instruction"] = sys_inst.strip()

        active_skills = skills if skills is not None else self.skills

        # Xây dựng danh sách nguồn files (Skills + Tệp người dùng đính kèm)
        sources = []
        for s_name, s_info in active_skills.items():
            s_type = s_info.get("type", "inline")
            if s_type == "skill_registry":
                sources.append({
                    "type": "skill_registry",
                    "source": s_info.get("source", ""),
                    "target": f".agents/skills/{s_name}"
                })
            else:
                sources.append({
                    "type": "inline",
                    "target": f".agents/skills/{s_name}/SKILL.md",
                    "content": s_info.get("content", "")
                })

        if extra_sources:
            sources.extend(extra_sources)

        clean_id = self.env_id.replace("environments/", "").strip() if self.env_id else None

        if not clean_id:
            if sources:
                kwargs["environment"] = {
                    "type": "remote",
                    "sources": sources
                }
            else:
                kwargs["environment"] = "remote"
        else:
            kwargs["environment"] = {
                "type": "remote",
                "environment_id": clean_id
            }
            if self.last_interaction_id:
                kwargs["previous_interaction_id"] = self.last_interaction_id

        try:
            interaction = self.client.interactions.create(**kwargs)
            self.env_id = interaction.environment_id or clean_id
            self.last_interaction_id = interaction.id
            return interaction
        except Exception as e:
            err_msg = str(e)
            # Tự động khắc phục lỗi 404 nếu Sandbox cũ bị hết hạn (Expired) hoặc bị xóa trên Google Cloud
            if clean_id and ("404" in err_msg or "not_found" in err_msg.lower() or "not found" in err_msg.lower()):
                self.old_expired_id = clean_id
                self.auto_recreated = True
                self.env_id = None
                kwargs.pop("previous_interaction_id", None)
                if sources:
                    kwargs["environment"] = {
                        "type": "remote",
                        "sources": sources
                    }
                else:
                    kwargs["environment"] = "remote"

                # Thử lại ngay lập tức với Sandbox mới
                interaction = self.client.interactions.create(**kwargs)
                self.env_id = interaction.environment_id
                self.last_interaction_id = interaction.id
                return interaction
            else:
                raise e

# Lưu trữ phiên làm việc đang chạy (session_id -> ManagedAgentSession)
active_sessions_agents = {}

def get_current_env_id(cur_id, sessions=None):
    if cur_id in active_sessions_agents and active_sessions_agents[cur_id].env_id:
        return active_sessions_agents[cur_id].env_id
    if sessions and cur_id in sessions and sessions[cur_id].get("env_id"):
        return sessions[cur_id].get("env_id")
    return None

# Đồng bộ trực tiếp Skill mới vào Sandbox đang chạy
def sync_skill_to_active_sandbox(api_key: str, env_id: str, skill_name: str, skill_content: str):
    if not env_id or not api_key:
        return False, "Chưa có sandbox"
    clean_env = env_id.replace("environments/", "").strip()
    remote_path = f".agents/skills/{skill_name}/SKILL.md"
    try:
        client = genai.Client(api_key=api_key)
        client.environments.files.upload(
            environment=clean_env,
            path=remote_path,
            file=skill_content.encode("utf-8")
        )
        return True, f"Đã đồng bộ `{remote_path}` vào Sandbox Cloud thành công!"
    except Exception as e:
        return False, str(e)

# --- Bộ xử lý bóc tách các bước tư duy, lệnh thực thi và kết quả công cụ ---
def format_interaction_steps(interaction):
    steps = getattr(interaction, "steps", []) or []
    thought_blocks = []
    exec_blocks = []

    for idx, step in enumerate(steps, start=1):
        step_type = getattr(step, "type", "") or step.__class__.__name__

        # 1. Thought Step (Tư duy)
        if step_type == "thought" or "Thought" in step_type:
            summary = getattr(step, "summary", [])
            for item in summary:
                txt = getattr(item, "text", str(item)).strip()
                if txt:
                    thought_blocks.append(txt)

        # 2. Code Execution (Chạy mã Python/Bash)
        elif "CodeExecutionCall" in step_type or step_type == "code_execution_call":
            args = getattr(step, "arguments", None)
            code = getattr(args, "code", "") if args else ""
            lang = getattr(args, "language", "python") if args else "python"
            exec_blocks.append(f"💻 **[Bước {idx}] Thực thi mã ({lang}):**\n```{lang}\n{code}\n```")

        elif "CodeExecutionResult" in step_type or step_type == "code_execution_result":
            res = getattr(step, "result", "")
            is_err = getattr(step, "is_error", False)
            tag = "❌ **Lỗi thực thi (Terminal Error):**" if is_err else "📋 **Kết quả Terminal (Output):**"
            exec_blocks.append(f"{tag}\n```text\n{res}\n```")

        # 3. Google Search
        elif "GoogleSearchCall" in step_type or step_type == "google_search_call":
            args = getattr(step, "arguments", None)
            queries = getattr(args, "queries", getattr(args, "query", str(args))) if args else ""
            exec_blocks.append(f"🔍 **[Bước {idx}] Google Search:** `{queries}`")

        elif "GoogleSearchResult" in step_type or step_type == "google_search_result":
            res = getattr(step, "result", "")
            exec_blocks.append(f"📄 **Kết quả Google Search:**\n```text\n{str(res)[:600]}\n```")

        # 4. Function / Tool Calls
        elif "FunctionCall" in step_type or step_type == "function_call":
            call = getattr(step, "call", getattr(step, "name", str(step)))
            exec_blocks.append(f"🛠️ **[Bước {idx}] Gọi Tool:** `{call}`")

        elif "FunctionResult" in step_type or step_type == "function_result":
            res = getattr(step, "result", "")
            exec_blocks.append(f"📦 **Kết quả Tool:**\n```text\n{str(res)[:600]}\n```")

        # Fallback summary
        elif hasattr(step, "summary") and step.summary:
            for item in step.summary:
                txt = getattr(item, "text", str(item)).strip()
                if txt:
                    thought_blocks.append(txt)

    result_md = ""
    if thought_blocks:
        thoughts_text = "\n\n".join(thought_blocks)
        result_md += f"<details>\n<summary>💭 <b>Xem các bước tư duy của Agent ({len(thought_blocks)} bước)</b></summary>\n\n{thoughts_text}\n\n</details>\n\n"

    if exec_blocks:
        exec_text = "\n\n".join(exec_blocks)
        result_md += f"<details>\n<summary>⚡ <b>Xem chi tiết Lệnh & Công cụ đã thực thi ({len(exec_blocks)} hành động)</b></summary>\n\n{exec_text}\n\n</details>\n\n"

    return result_md

# --- Quản lý Tệp Sandbox (File Explorer) ---
def list_sandbox_files(api_key: str, cur_id: str, sessions=None):
    key = api_key.strip() or colab_api_key or os.environ.get("GEMINI_API_KEY", "")
    env_id = get_current_env_id(cur_id, sessions)
    if not key:
        return gr.update(choices=[]), "⚠️ Vui lòng nhập Gemini API Key."
    if not env_id:
        return gr.update(choices=[]), "ℹ️ Phiên này chưa gửi câu hỏi nào hoặc chưa gắn Sandbox Cloud."

    clean_env = env_id.replace("environments/", "").strip()
    target = f"environments/{clean_env}"
    headers = {"x-goog-api-key": key, "Content-Type": "application/json"}
    url = f"https://generativelanguage.googleapis.com/v1beta/{target}/files"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return gr.update(choices=[]), f"⚠️ Lỗi Google API ({res.status_code}): {res.text}"
        files_data = res.json().get("files", [])
        if not files_data:
            return gr.update(choices=[]), f"📁 Sandbox `{clean_env}` hiện tại chưa có tệp nào."

        file_list = []
        md_lines = [f"### 📂 Danh sách tệp trong Sandbox (`{clean_env}`):\n"]
        for idx, f in enumerate(files_data, start=1):
            name = f.get("name") or f.get("path") or f"file_{idx}"
            size = f.get("sizeBytes") or f.get("size_bytes", "0")
            file_list.append(name)
            md_lines.append(f"{idx}. 📄 `{name}` — **{int(size):,} bytes**")
        return gr.update(choices=file_list, value=file_list[0] if file_list else None), "\n".join(md_lines)
    except Exception as e:
        return gr.update(choices=[]), f"❌ Lỗi truy vấn tệp: {str(e)}"

def download_file_from_sandbox(api_key: str, cur_id: str, selected_file: str, custom_file_name: str, sessions=None):
    key = api_key.strip() or colab_api_key or os.environ.get("GEMINI_API_KEY", "")
    env_id = get_current_env_id(cur_id, sessions)
    if not key or not env_id:
        return "⚠️ Cần có Gemini API Key và Sandbox ID hợp lệ để tải tệp."

    file_to_get = (custom_file_name.strip() if custom_file_name and custom_file_name.strip() else selected_file) or ""
    if not file_to_get:
        return "⚠️ Vui lòng chọn hoặc nhập tên file cần tải."

    clean_env = env_id.replace("environments/", "").strip()
    clean_path = file_to_get.lstrip("/")

    data = None
    err_log = []

    # 1. Thử dùng SDK chính thức
    try:
        client = genai.Client(api_key=key)
        data = client.environments.files.download(environment=clean_env, path=clean_path)
    except Exception as e:
        err_log.append(f"SDK: {e}")

    # 2. Dự phòng dùng REST API trực tiếp
    if data is None:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/environments/{clean_env}/files/{clean_path}?alt=media"
            headers = {"x-goog-api-key": key}
            res = requests.get(url, headers=headers, timeout=30)
            if res.status_code == 200:
                data = res.content
            else:
                err_log.append(f"REST ({res.status_code}): {res.text}")
        except Exception as e:
            err_log.append(f"REST error: {e}")

    if data is not None:
        filename = os.path.basename(clean_path) or "downloaded_file"
        save_path = os.path.join(COLAB_DOWNLOAD_DIR, filename)
        with open(save_path, "wb") as f:
            f.write(data)
        return f"🎉 **Đã tải thành công tệp về Colab!**\n- 📍 **Đường dẫn lưu**: `{save_path}`\n- ⚖️ **Kích thước**: **{len(data):,} bytes**\n*(Bạn có thể xem tệp trực tiếp trong thanh thư mục bên trái của Google Colab)*"
    else:
        return f"❌ Không thể tải file `{clean_path}`. Chi tiết: {'; '.join(err_log)}"

def upload_file_to_sandbox(api_key: str, cur_id: str, upload_obj, colab_path_input: str, target_name: str, sessions=None):
    key = api_key.strip() or colab_api_key or os.environ.get("GEMINI_API_KEY", "")
    env_id = get_current_env_id(cur_id, sessions)
    if not key or not env_id:
        return "⚠️ Cần có Gemini API Key và Sandbox ID hợp lệ để tải tệp lên. Hãy gửi 1 câu hỏi hoặc kết nối Sandbox trước!"

    data_bytes = None
    source_filename = ""

    if upload_obj is not None:
        file_path = upload_obj.name if hasattr(upload_obj, "name") else str(upload_obj)
        source_filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            data_bytes = f.read()
    elif colab_path_input and colab_path_input.strip():
        cp = colab_path_input.strip()
        if os.path.exists(cp):
            source_filename = os.path.basename(cp)
            with open(cp, "rb") as f:
                data_bytes = f.read()
        else:
            return f"❌ Không tìm thấy tệp tại đường dẫn Colab: `{cp}`"
    else:
        return "⚠️ Vui lòng chọn tệp tải lên hoặc nhập đường dẫn tệp trên Colab."

    dest_name = target_name.strip() if target_name and target_name.strip() else source_filename
    clean_env = env_id.replace("environments/", "").strip()

    try:
        client = genai.Client(api_key=key)
        client.environments.files.upload(environment=clean_env, path=dest_name, file=data_bytes)
        return f"✅ **Đã tải tệp lên Sandbox Cloud thành công!**\n- Tên tệp trong Sandbox: `{dest_name}`\n- Dung lượng: **{len(data_bytes):,} bytes**"
    except Exception as e:
        return f"❌ Lỗi khi tải tệp lên: {str(e)}"

# --- Quản lý & Kết nối Sandbox Cloud Google (Quay lại Sandbox cũ / Xóa chọn lọc / Kiểm tra trạng thái) ---
def get_all_cloud_sandboxes(api_key: str):
    key = api_key.strip() or colab_api_key or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        return [], "⚠️ Vui lòng nhập Gemini API Key để quét Sandbox."
    headers = {"x-goog-api-key": key, "Content-Type": "application/json"}
    url = "https://generativelanguage.googleapis.com/v1beta/environments?pageSize=50"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return [], f"⚠️ Lỗi kết nối Google API ({res.status_code}): {res.text}"
        envs = res.json().get("environments", [])
        env_choices = []
        active_count = 0
        for env in envs:
            raw_id = env.get("name") or env.get("id") or env.get("environmentId", "")
            clean_id = raw_id.replace("environments/", "").strip()
            if clean_id:
                status = env.get("status", "unknown")
                file_cnt = env.get("file_count", 0)
                if status == "active":
                    active_count += 1
                    env_choices.append((f"🟢 {clean_id} (Hoạt động | {file_cnt} tệp)", clean_id))
                elif status == "expired":
                    env_choices.append((f"🔴 {clean_id} (Đã hết hạn)", clean_id))
                else:
                    env_choices.append((f"⚪ {clean_id}", clean_id))
        if not env_choices:
            return [], "🎉 Hiện không có Sandbox nào đang chạy trên Google Cloud."
        # Đưa các sandbox đang active lên đầu
        env_choices.sort(key=lambda x: 0 if "🟢" in x[0] else 1)
        return env_choices, f"📋 Đang có **{len(env_choices)}** Sandbox ({active_count} đang hoạt động) trên Google Cloud."
    except Exception as e:
        return [], f"❌ Lỗi: {str(e)}"

def attach_to_existing_sandbox(api_key: str, cur_id: str, selected_sandbox: str, custom_sandbox: str, sessions):
    key = api_key.strip() or colab_api_key or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        return sessions, gr.update(), "⚠️ Vui lòng nhập Gemini API Key trước khi kết nối.", "ℹ️ Chưa có Sandbox ID"

    target = (custom_sandbox.strip() if custom_sandbox and custom_sandbox.strip() else selected_sandbox) or ""
    if not target:
        return sessions, gr.update(), "⚠️ Vui lòng chọn hoặc nhập mã Sandbox ID cần kết nối.", "ℹ️ Chưa có Sandbox ID"

    clean_target = target.replace("environments/", "").strip()

    # Kiểm tra trạng thái Sandbox trên Google Cloud trước khi kết nối
    headers = {"x-goog-api-key": key, "Content-Type": "application/json"}
    url = f"https://generativelanguage.googleapis.com/v1beta/environments/{clean_target}"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 404:
            return sessions, gr.update(), f"❌ Sandbox `{clean_target}` không tồn tại trên Google Cloud (có thể đã bị xóa hoặc sai ID).", gr.update()
        elif res.status_code == 200:
            env_info = res.json()
            status = env_info.get("status", "")
            if status == "expired":
                return sessions, gr.update(), f"⚠️ Sandbox `{clean_target}` đã **HẾT HẠN (expired)** trên Google Cloud.\nGoogle tự động thu hồi Sandbox sau một khoảng thời gian không dùng. Vui lòng chọn một Sandbox có nhãn 🟢 Hoạt động hoặc gửi tin nhắn để hệ thống tự cấp phát Sandbox mới!", gr.update()
    except Exception:
        pass

    # Cập nhật phiên với clean ID này
    sessions[cur_id]["env_id"] = clean_target
    if cur_id in active_sessions_agents:
        active_sessions_agents[cur_id].env_id = clean_target
        active_sessions_agents[cur_id].last_interaction_id = None
        active_sessions_agents[cur_id].step = 0

    badge_text = f"🌐 **Sandbox ID:** `{clean_target}` *(Đã gắn kết nối Sandbox cũ)*"
    status_msg = f"🎉 **Đã kết nối thành công vào Sandbox:** `{clean_target}`!\nAgent sẽ làm việc tiếp trên môi trường và các tệp có sẵn trong Sandbox này."

    return sessions, clean_target, status_msg, badge_text

def delete_specific_sandbox(api_key: str, selected_sandbox: str, sessions, cur_id):
    key = api_key.strip() or colab_api_key or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        return sessions, gr.update(), gr.update(), "⚠️ Vui lòng nhập Gemini API Key.", gr.update()
    if not selected_sandbox:
        return sessions, gr.update(), gr.update(), "⚠️ Vui lòng chọn Sandbox cần xóa.", gr.update()

    clean_target = selected_sandbox.replace("environments/", "").strip()
    headers = {"x-goog-api-key": key, "Content-Type": "application/json"}
    url = f"https://generativelanguage.googleapis.com/v1beta/environments/{clean_target}"
    try:
        res = requests.delete(url, headers=headers, timeout=10)
        if res.status_code in (200, 204):
            if sessions.get(cur_id, {}).get("env_id") == clean_target:
                sessions[cur_id]["env_id"] = None
            if cur_id in active_sessions_agents and active_sessions_agents[cur_id].env_id == clean_target:
                active_sessions_agents[cur_id].env_id = None

            env_choices, _ = get_all_cloud_sandboxes(key)
            new_val = env_choices[0][1] if env_choices else None
            return (
                sessions,
                gr.update(choices=env_choices, value=new_val),
                gr.update(choices=env_choices, value=new_val),
                f"🗑️ **Đã xóa thành công Sandbox:** `{clean_target}`",
                "ℹ️ *Chưa có Sandbox ID*"
            )
        else:
            return sessions, gr.update(), gr.update(), f"❌ Không thể xóa Sandbox ({res.status_code}): {res.text}", gr.update()
    except Exception as e:
        return sessions, gr.update(), gr.update(), f"❌ Lỗi khi xóa: {str(e)}", gr.update()

def inspect_cloud_sandboxes(api_key: str):
    key = api_key.strip() or colab_api_key or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        return "⚠️ Vui lòng nhập Gemini API Key để kiểm tra."
    headers = {"x-goog-api-key": key, "Content-Type": "application/json"}
    url = "https://generativelanguage.googleapis.com/v1beta/environments?pageSize=50"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return f"⚠️ Lỗi kết nối Google API ({res.status_code}): {res.text}"
        envs = res.json().get("environments", [])
        if not envs:
            return "🎉 Tài khoản sạch sẽ, không có sandbox nào."
        details = [f"### 📋 Chi tiết {len(envs)} Sandbox trên Google Cloud:\n"]
        for idx, env in enumerate(envs, start=1):
            raw_id = env.get("name") or env.get("id") or env.get("environmentId", "")
            clean_id = raw_id.replace("environments/", "").strip()
            status = env.get("status", "unknown")
            status_icon = "🟢 Hoạt động" if status == "active" else "🔴 Đã hết hạn"
            details.append(f"#### {idx}. Sandbox: `{clean_id}` ({status_icon})")
            files_url = f"https://generativelanguage.googleapis.com/v1beta/environments/{clean_id}/files"
            try:
                f_res = requests.get(files_url, headers=headers, timeout=5)
                if f_res.status_code == 200:
                    files_data = f_res.json().get("files", [])
                    if files_data:
                        details.append(f"- **Tệp ({len(files_data)})**:\n  " + "\n  ".join(f"• `{f.get('name', 'file')}` ({f.get('sizeBytes', '0')} B)" for f in files_data[:15]))
                    else:
                        details.append("- **Tệp**: *(Trống)*")
                else:
                    details.append("- **Tệp**: *(Không có tệp)*")
            except Exception:
                details.append("- **Tệp**: *(Không truy xuất được)*")
            details.append("")
        return "\n".join(details)
    except Exception as e:
        return f"❌ Lỗi: {str(e)}"

def clean_all_cloud_sandboxes(api_key: str, sessions):
    key = api_key.strip() or colab_api_key or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        return sessions, gr.update(choices=[], value=None), gr.update(choices=[], value=None), "⚠️ Vui lòng nhập Gemini API Key để thực hiện.", "ℹ️ *Chưa có Sandbox ID*"
    headers = {"x-goog-api-key": key, "Content-Type": "application/json"}
    url = "https://generativelanguage.googleapis.com/v1beta/environments?pageSize=50"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return sessions, gr.update(choices=[]), gr.update(choices=[]), f"⚠️ Lỗi kết nối Google API ({res.status_code}): {res.text}", gr.update()
        envs = res.json().get("environments", [])
        if not envs:
            return sessions, gr.update(choices=[]), gr.update(choices=[]), "🎉 Tài khoản sạch sẽ! Không có sandbox cloud nào cần xóa.", gr.update()
        deleted_count = 0
        for env in envs:
            raw_id = env.get("name") or env.get("id") or env.get("environmentId", "")
            clean_id = raw_id.replace("environments/", "").strip()
            if clean_id:
                del_url = f"https://generativelanguage.googleapis.com/v1beta/environments/{clean_id}"
                del_res = requests.delete(del_url, headers=headers, timeout=10)
                if del_res.status_code in (200, 204):
                    deleted_count += 1
        active_sessions_agents.clear()
        for s in sessions.values():
            s["env_id"] = None
        return (
            sessions,
            gr.update(choices=[], value=None),
            gr.update(choices=[], value=None),
            f"✨ Đã xóa sạch {deleted_count}/{len(envs)} sandbox cloud! Đã giải phóng 100% dung lượng và quota Google.",
            "ℹ️ *Chưa có Sandbox ID*"
        )
    except Exception as e:
        return sessions, gr.update(), gr.update(), f"❌ Lỗi khi dọn dẹp: {str(e)}", gr.update()

# --- Quản lý Lưu trữ / Phục hồi Phiên làm việc (Session Persistence) ---
def init_sessions():
    first_id = uuid.uuid4().hex
    return {first_id: {"name": "Phiên #1 (Mặc định)", "history": [], "system_prompt": "", "skills": {}, "env_id": None}}, first_id

def render_active_skills_markdown(skills_dict):
    if not skills_dict:
        return "*(Chưa kích hoạt Kỹ năng nào trong phiên này)*"
    lines = ["**Kỹ năng đang hoạt động trong phiên:**"]
    for s_name, s_info in skills_dict.items():
        desc = s_info.get("desc") or "Kỹ năng mở rộng"
        s_type = "Cloud Registry" if s_info.get("type") == "skill_registry" else "Local SKILL.md"
        lines.append(f"- 🧩 **`{s_name}`** ({s_type}): *{desc}*")
    return "\n".join(lines)

def save_sessions_backup(sessions):
    try:
        with open(BACKUP_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
        return f"💾 **Đã lưu an toàn {len(sessions)} phiên làm việc (kèm Skills & Sandbox ID)!**\n- File sao lưu: `{BACKUP_FILE}`"
    except Exception as e:
        return f"❌ Lỗi khi sao lưu phiên: {str(e)}"

def load_sessions_backup():
    if not os.path.exists(BACKUP_FILE):
        return None, None, None, f"⚠️ Chưa tìm thấy file sao lưu tại: `{BACKUP_FILE}`"
    try:
        with open(BACKUP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data or not isinstance(data, dict):
            return None, None, None, "⚠️ File sao lưu không hợp lệ."
        first_id = list(data.keys())[0]
        choices = [s.get("name", "Phiên") for s in data.values()]
        return data, first_id, choices, f"✅ **Đã khôi phục thành công {len(data)} phiên làm việc từ file sao lưu!**"
    except Exception as e:
        return None, None, None, f"❌ Lỗi đọc file: {str(e)}"

def export_session_markdown(sessions, cur_id):
    session_data = sessions.get(cur_id, {})
    history = session_data.get("history", [])
    sess_name = session_data.get("name", "Phiên")
    skills = session_data.get("skills", {})
    env_id = session_data.get("env_id")
    if not history:
        return "⚠️ Phiên hiện tại chưa có tin nhắn nào để xuất."
    lines = [f"# Lịch sử hội thoại - {sess_name}\n"]
    if env_id:
        lines.append(f"**Sandbox ID:** `{env_id}`\n")
    if skills:
        lines.append("## Kỹ năng kích hoạt:")
        for s_name, s_info in skills.items():
            lines.append(f"- {s_name}: {s_info.get('desc', '')}")
        lines.append("")
    for turn in history:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        lines.append(f"### {'👤 Bạn' if role == 'user' else '🛸 Agent'}:\n{content}\n")
    safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in sess_name)
    export_path = f"/content/{safe_name}_{cur_id[:6]}.md"
    try:
        with open(export_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return f"💾 **Đã xuất file Markdown thành công!**\n- Đường dẫn tại Colab: `{export_path}`"
    except Exception as e:
        return f"❌ Lỗi xuất file: {str(e)}"

# --- Khởi tạo Giao diện Gradio ---
with gr.Blocks(title="Google Antigravity Agent Studio Pro") as demo:
    init_dict, init_id = init_sessions()
    sessions_state = gr.State(init_dict)
    current_session_id = gr.State(init_id)

    gr.Markdown("""
    # 🛸 Google Antigravity Managed Agent Studio Pro (v3.5)
    Sử dụng chính thức **Google Managed Antigravity Engine** (`antigravity-preview-05-2026`) trên Google Cloud.
    ✨ **Các tính năng Pro:** Đính kèm tất cả các loại tệp (Ảnh, PDF, CSV, Excel, Code, ZIP...), Dán ảnh trực tiếp (Ctrl+V), Tự động phục hồi khi Sandbox hết hạn (Self-Healing Fallback), Quay trở lại Sandbox cũ, Chọn Sandbox cụ thể để xóa, Quản lý Kỹ năng (Agent Skills & Registry), Quản lý tệp Sandbox 2 chiều (tải về `/content/`).
    """)

    with gr.Row():
        # --- CỘT ĐIỀU KHIỂN BÊN TRÁI ---
        with gr.Column(scale=1):
            gr.Markdown("### 🗂️ Quản lý phiên hội thoại")
            session_dropdown = gr.Dropdown(
                label="Chọn phiên làm việc",
                choices=["Phiên #1 (Mặc định)"],
                value="Phiên #1 (Mặc định)",
                interactive=True
            )
            with gr.Row():
                new_session_btn = gr.Button("➕ Phiên mới", size="sm", variant="secondary")
                delete_session_btn = gr.Button("🗑️ Xóa phiên", size="sm")

            # Mục 1: Hộp công cụ Sandbox & Tệp tin Cloud (Gom Sandbox + File Explorer)
            with gr.Accordion("📦 Quản lý Sandbox & Tệp tin Cloud (Sandbox & Files)", open=True):
                current_sandbox_display = gr.Markdown("🌐 **Sandbox hiện tại:** *(Chưa kết nối - sẽ tự cấp phát khi gửi tin nhắn)*")

                with gr.Tab("📁 Tệp tin Sandbox (File Explorer)"):
                    gr.Markdown("Duyệt và tải tệp từ Cloud Sandbox về thư mục `/content/` của Colab:")
                    refresh_files_btn = gr.Button("🔄 Quét tệp trong Sandbox hiện tại", size="sm", variant="secondary")
                    sandbox_files_md = gr.Markdown("*(Bấm quét để xem danh sách tệp)*")
                    sandbox_file_choice = gr.Dropdown(label="Chọn tệp cần tải về Colab", choices=[])
                    custom_download_input = gr.Textbox(label="Hoặc nhập tên tệp tùy ý", placeholder="main.py, report.txt...")
                    download_to_colab_btn = gr.Button("📥 Tải tệp về thư mục /content/ Colab", size="sm", variant="primary")
                    file_action_status = gr.Markdown("")

                    gr.Markdown("---")
                    gr.Markdown("**Tải tệp từ Colab lên Sandbox Cloud:**")
                    upload_file_widget = gr.File(label="Chọn tệp từ máy / Colab", file_count="single")
                    colab_file_path = gr.Textbox(label="Hoặc nhập đường dẫn tệp trên Colab", placeholder="/content/data.csv")
                    sandbox_dest_name = gr.Textbox(label="Tên lưu trên Sandbox (tùy chọn)", placeholder="data.csv")
                    upload_to_sandbox_btn = gr.Button("📤 Đẩy tệp lên Sandbox", size="sm")

                with gr.Tab("☁️ Kết nối & Dọn dẹp Sandbox"):
                    refresh_cloud_sandboxes_btn = gr.Button("🔄 Quét danh sách Sandbox Cloud", size="sm", variant="secondary")

                    gr.Markdown("---")
                    gr.Markdown("**1. Quay lại làm việc trên Sandbox cũ:**")
                    existing_sandboxes_dropdown = gr.Dropdown(label="Chọn Sandbox trên Cloud (🟢 Hoạt động | 🔴 Hết hạn)", choices=[])
                    custom_sandbox_text = gr.Textbox(label="Hoặc dán Sandbox ID (vd: env_...)", placeholder="env_...")
                    attach_sandbox_btn = gr.Button("🔗 Kết nối vào Sandbox này", size="sm", variant="primary")

                    gr.Markdown("---")
                    gr.Markdown("**2. Chọn Sandbox cụ thể để xóa:**")
                    delete_target_dropdown = gr.Dropdown(label="Chọn Sandbox cần xóa", choices=[])
                    delete_specific_btn = gr.Button("🗑️ Xóa Sandbox đã chọn", size="sm")

                    gr.Markdown("---")
                    with gr.Row():
                        inspect_cloud_btn = gr.Button("🔍 Chi tiết", size="sm")
                        clean_all_sandboxes_btn = gr.Button("🧹 Xóa tất cả Sandbox", size="sm", variant="stop")

                    sandbox_action_status = gr.Markdown("")

            # Mục 2: Quản lý Kỹ năng (Agent Skills)
            with gr.Accordion("🧩 Quản lý Kỹ năng (Agent Skills)", open=False):
                gr.Markdown("Kỹ năng cung cấp quy trình chuyên sâu cho Agent (`.agents/skills/`):")
                active_skills_display = gr.Markdown("*(Chưa kích hoạt Kỹ năng nào trong phiên này)*")

                with gr.Tab("Thư viện Mẫu"):
                    skill_sample_dropdown = gr.Dropdown(
                        label="Chọn Kỹ năng Mẫu",
                        choices=list(CURATED_SKILLS.keys()),
                        value="data-analyst-pro"
                    )
                    add_sample_skill_btn = gr.Button("✨ Kích hoạt Kỹ năng này", size="sm", variant="secondary")

                with gr.Tab("Tạo mới / Tùy chỉnh"):
                    custom_skill_name_input = gr.Textbox(label="Tên Kỹ năng (ID)", placeholder="vd: crypto-analyzer, report-bot...")
                    custom_skill_desc_input = gr.Textbox(label="Mô tả Kỹ năng", placeholder="Mô tả ngắn...")
                    custom_skill_content_input = gr.Textbox(
                        label="Nội dung SKILL.md",
                        lines=5,
                        placeholder="# Hướng dẫn thực hiện quy trình...\n- Bước 1: ...\n- Bước 2: ..."
                    )
                    create_custom_skill_btn = gr.Button("➕ Tạo & Gắn Kỹ năng", size="sm")

                with gr.Tab("Cloud Registry"):
                    skill_registry_input = gr.Textbox(
                        label="Skill Resource Name (GCP)",
                        placeholder="projects/{project}/locations/{location}/skills/{skill_id}"
                    )
                    skill_registry_id_input = gr.Textbox(label="Tên định danh trong Sandbox", placeholder="my-gcp-skill")
                    add_registry_skill_btn = gr.Button("🔗 Gắn từ Registry", size="sm")

                with gr.Row():
                    remove_skill_dropdown = gr.Dropdown(label="Chọn Skill để gỡ", choices=[])
                    remove_skill_btn = gr.Button("🗑️ Gỡ bỏ", size="sm")

                skill_action_status = gr.Markdown("")

            # Mục 3: Cấu hình Model & Vai trò (System Instruction)
            with gr.Accordion("⚙️ Cấu hình Agent & System Instruction", open=False):
                api_key_input = gr.Textbox(
                    label="Gemini API Key",
                    placeholder="Nhập Key nếu chưa lưu trong Colab Secrets...",
                    value=colab_api_key,
                    type="password"
                )
                agent_select = gr.Dropdown(
                    label="Lựa chọn Agent",
                    choices=AVAILABLE_AGENTS,
                    value=DEFAULT_AGENT,
                    interactive=True
                )
                custom_agent_box = gr.Textbox(
                    label="Nhập tên Agent tùy chỉnh",
                    placeholder="Nhập mã model hoặc agent...",
                    visible=False
                )
                system_instruction_input = gr.Textbox(
                    label="Chỉ dẫn hệ thống (System Instruction)",
                    placeholder="Ví dụ: Bạn là một lập trình viên Fullstack hàng đầu, hãy ưu tiên viết mã hoàn chỉnh và giải thích ngắn gọn...",
                    lines=3
                )



            # Mục 5: Sao lưu & Phục hồi phiên (Persistence)
            with gr.Accordion("💾 Sao lưu & Phục hồi Phiên (Persistence)", open=False):
                with gr.Row():
                    save_backup_btn = gr.Button("💾 Lưu tất cả phiên", size="sm", variant="secondary")
                    load_backup_btn = gr.Button("📂 Phục hồi từ sao lưu", size="sm")
                export_md_btn = gr.Button("📄 Xuất Markdown phiên hiện tại", size="sm")
                backup_status = gr.Markdown(f"File sao lưu mặc định: `{BACKUP_FILE}`")

        # --- CỘT CHAT BÊN PHẢI ---
        with gr.Column(scale=3):
            session_title_md = gr.Markdown("### 💬 Trò chuyện: Phiên #1 (Mặc định)")
            session_env_info = gr.Markdown("ℹ️ *Chưa có Sandbox ID (sẽ tự động cấp phát khi gửi tin nhắn đầu tiên hoặc bấm kết nối ở cột trái)*")
            chatbot = gr.Chatbot(height=520, show_label=False)
            msg_input = gr.MultimodalTextbox(
                placeholder="Nhập câu hỏi, dán ảnh (Ctrl+V) hoặc bấm biểu tượng đính kèm để gửi bất kỳ tệp nào (PDF, CSV, Excel, Code, ZIP, TXT...)...",
                file_count="multiple",
                show_label=False,
                autofocus=True
            )
            with gr.Row():
                submit_btn = gr.Button("🚀 Gửi yêu cầu", variant="primary")
                clear_btn = gr.Button("🧹 Xóa tin nhắn trong phiên")

    # --- Xử lý logic Agent Dropdown tùy chỉnh ---
    def on_agent_select_change(choice):
        return gr.update(visible=(choice == "Tùy chỉnh khác..."))

    agent_select.change(on_agent_select_change, inputs=[agent_select], outputs=[custom_agent_box])

    # --- Xử lý Quản lý & Kết nối Sandbox Cloud ---
    def on_refresh_cloud_sandboxes(api_key):
        env_choices, msg = get_all_cloud_sandboxes(api_key)
        val = env_choices[0][1] if env_choices else None
        return gr.update(choices=env_choices, value=val), gr.update(choices=env_choices, value=val), msg

    refresh_cloud_sandboxes_btn.click(
        on_refresh_cloud_sandboxes,
        inputs=[api_key_input],
        outputs=[existing_sandboxes_dropdown, delete_target_dropdown, sandbox_action_status]
    )

    def on_attach_sandbox(api_key, cur_id, selected_sb, custom_sb, sessions):
        sessions, target_id, msg, badge_txt = attach_to_existing_sandbox(api_key, cur_id, selected_sb, custom_sb, sessions)
        return sessions, f"🌐 **Sandbox hiện tại:** `{target_id}`", msg, badge_txt

    attach_sandbox_btn.click(
        on_attach_sandbox,
        inputs=[api_key_input, current_session_id, existing_sandboxes_dropdown, custom_sandbox_text, sessions_state],
        outputs=[sessions_state, current_sandbox_display, sandbox_action_status, session_env_info]
    ).then(
        list_sandbox_files,
        inputs=[api_key_input, current_session_id, sessions_state],
        outputs=[sandbox_file_choice, sandbox_files_md]
    )

    delete_specific_btn.click(
        delete_specific_sandbox,
        inputs=[api_key_input, delete_target_dropdown, sessions_state, current_session_id],
        outputs=[sessions_state, existing_sandboxes_dropdown, delete_target_dropdown, sandbox_action_status, session_env_info]
    )

    clean_all_sandboxes_btn.click(
        clean_all_cloud_sandboxes,
        inputs=[api_key_input, sessions_state],
        outputs=[sessions_state, existing_sandboxes_dropdown, delete_target_dropdown, sandbox_action_status, session_env_info]
    )

    inspect_cloud_btn.click(inspect_cloud_sandboxes, inputs=[api_key_input], outputs=[sandbox_action_status])

    # --- Xử lý các sự kiện Kỹ năng (Skill Management) ---
    def on_add_sample_skill(sample_choice, sessions, cur_id, api_key):
        if not sample_choice or sample_choice not in CURATED_SKILLS:
            return sessions, gr.update(), gr.update(), "⚠️ Vui lòng chọn kỹ năng mẫu hợp lệ."
        skill_data = CURATED_SKILLS[sample_choice]
        if "skills" not in sessions[cur_id]:
            sessions[cur_id]["skills"] = {}
        sessions[cur_id]["skills"][sample_choice] = skill_data

        env_id = get_current_env_id(cur_id, sessions)
        active_key = api_key.strip() or colab_api_key or os.environ.get("GEMINI_API_KEY", "")
        sync_msg = ""
        if env_id and active_key:
            ok, msg = sync_skill_to_active_sandbox(active_key, env_id, sample_choice, skill_data["content"])
            sync_msg = f" và {msg}" if ok else f" (Lưu ý: chưa đồng bộ được vào sandbox: {msg})"

        updated_skills = sessions[cur_id]["skills"]
        md = render_active_skills_markdown(updated_skills)
        choices = list(updated_skills.keys())
        return sessions, md, gr.update(choices=choices, value=choices[-1] if choices else None), f"✅ Đã kích hoạt kỹ năng `{sample_choice}`{sync_msg}!"

    def on_create_custom_skill(name, desc, content, sessions, cur_id, api_key):
        clean_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in str(name).strip().lower())
        if not clean_name:
            return sessions, gr.update(), gr.update(), "⚠️ Tên Kỹ năng không hợp lệ."
        if not content or not content.strip():
            return sessions, gr.update(), gr.update(), "⚠️ Nội dung SKILL.md không được để trống."

        full_content = content.strip()
        if not full_content.startswith("---"):
            full_content = f"---\nname: {clean_name}\ndescription: {desc.strip() or clean_name}\n---\n\n" + full_content

        skill_data = {
            "name": clean_name,
            "desc": desc.strip() or clean_name,
            "type": "inline",
            "content": full_content
        }

        if "skills" not in sessions[cur_id]:
            sessions[cur_id]["skills"] = {}
        sessions[cur_id]["skills"][clean_name] = skill_data

        env_id = get_current_env_id(cur_id, sessions)
        active_key = api_key.strip() or colab_api_key or os.environ.get("GEMINI_API_KEY", "")
        sync_msg = ""
        if env_id and active_key:
            ok, msg = sync_skill_to_active_sandbox(active_key, env_id, clean_name, full_content)
            sync_msg = f" và {msg}" if ok else f" (Lưu ý: chưa đồng bộ được vào sandbox: {msg})"

        updated_skills = sessions[cur_id]["skills"]
        md = render_active_skills_markdown(updated_skills)
        choices = list(updated_skills.keys())
        return sessions, md, gr.update(choices=choices, value=choices[-1] if choices else None), f"✅ Đã tạo và gắn kỹ năng `{clean_name}`{sync_msg}!"

    def on_add_registry_skill(res_name, identifier, sessions, cur_id):
        res = str(res_name).strip()
        name = str(identifier).strip() or "registry-skill"
        if not res:
            return sessions, gr.update(), gr.update(), "⚠️ Vui lòng nhập Skill Resource Name từ GCP."
        clean_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name.lower())
        skill_data = {
            "name": clean_name,
            "desc": f"Enterprise Skill Registry ({res})",
            "type": "skill_registry",
            "source": res
        }
        if "skills" not in sessions[cur_id]:
            sessions[cur_id]["skills"] = {}
        sessions[cur_id]["skills"][clean_name] = skill_data
        updated_skills = sessions[cur_id]["skills"]
        md = render_active_skills_markdown(updated_skills)
        choices = list(updated_skills.keys())
        return sessions, md, gr.update(choices=choices, value=choices[-1] if choices else None), f"✅ Đã gắn Skill Registry `{clean_name}` thành công!"

    def on_remove_skill(skill_to_remove, sessions, cur_id):
        if not skill_to_remove or skill_to_remove not in sessions[cur_id].get("skills", {}):
            return sessions, gr.update(), gr.update(), "⚠️ Vui lòng chọn kỹ năng cần gỡ."
        del sessions[cur_id]["skills"][skill_to_remove]
        updated_skills = sessions[cur_id]["skills"]
        md = render_active_skills_markdown(updated_skills)
        choices = list(updated_skills.keys())
        return sessions, md, gr.update(choices=choices, value=choices[0] if choices else None), f"🗑️ Đã gỡ bỏ kỹ năng `{skill_to_remove}` khỏi phiên."

    add_sample_skill_btn.click(
        on_add_sample_skill,
        inputs=[skill_sample_dropdown, sessions_state, current_session_id, api_key_input],
        outputs=[sessions_state, active_skills_display, remove_skill_dropdown, skill_action_status]
    )
    create_custom_skill_btn.click(
        on_create_custom_skill,
        inputs=[custom_skill_name_input, custom_skill_desc_input, custom_skill_content_input, sessions_state, current_session_id, api_key_input],
        outputs=[sessions_state, active_skills_display, remove_skill_dropdown, skill_action_status]
    )
    add_registry_skill_btn.click(
        on_add_registry_skill,
        inputs=[skill_registry_input, skill_registry_id_input, sessions_state, current_session_id],
        outputs=[sessions_state, active_skills_display, remove_skill_dropdown, skill_action_status]
    )
    remove_skill_btn.click(
        on_remove_skill,
        inputs=[remove_skill_dropdown, sessions_state, current_session_id],
        outputs=[sessions_state, active_skills_display, remove_skill_dropdown, skill_action_status]
    )

    # --- Xử lý các sự kiện Phiên làm việc ---
    def on_new_session(sessions, cur_id):
        new_id = uuid.uuid4().hex
        name = f"Phiên #{len(sessions) + 1}"
        sessions[new_id] = {"name": name, "history": [], "system_prompt": "", "skills": {}, "env_id": None}
        choices = [s["name"] for s in sessions.values()]
        return (
            sessions, new_id, gr.update(choices=choices, value=name),
            f"### 💬 Trò chuyện: {name}", "ℹ️ *Phiên mới: Chưa có Sandbox ID*",
            [], "", "*(Chưa kích hoạt Kỹ năng nào trong phiên này)*", gr.update(choices=[], value=None),
            "🌐 **Sandbox hiện tại:** *(Chưa kết nối)*"
        )

    def on_switch_session(selected_name, sessions, cur_id):
        for s_id, s_data in sessions.items():
            if s_data["name"] == selected_name:
                active_env = get_current_env_id(s_id, sessions)
                env_txt = f"🌐 **Sandbox ID:** `{active_env}`" if active_env else "ℹ️ *Chưa có Sandbox ID (sẽ tự tạo hoặc bấm kết nối ở cột trái)*"
                sb_badge = f"🌐 **Sandbox hiện tại:** `{active_env}`" if active_env else "🌐 **Sandbox hiện tại:** *(Chưa kết nối)*"
                sys_prompt = s_data.get("system_prompt", "")
                skills_dict = s_data.get("skills", {})
                skills_md = render_active_skills_markdown(skills_dict)
                skill_choices = list(skills_dict.keys())
                return s_id, f"### 💬 Trò chuyện: {selected_name}", env_txt, s_data["history"], sys_prompt, skills_md, gr.update(choices=skill_choices, value=skill_choices[0] if skill_choices else None), sb_badge
        return cur_id, f"### 💬 Trò chuyện: {selected_name}", "", [], "", "", gr.update(choices=[]), "🌐 **Sandbox hiện tại:** *(Chưa kết nối)*"

    def on_delete_session(sessions, cur_id):
        if cur_id in active_sessions_agents:
            del active_sessions_agents[cur_id]
        if len(sessions) <= 1:
            first_id = list(sessions.keys())[0]
            sessions[first_id]["history"] = []
            sessions[first_id]["skills"] = {}
            sessions[first_id]["env_id"] = None
            return (
                sessions, first_id, gr.update(choices=[sessions[first_id]["name"]], value=sessions[first_id]["name"]),
                f"### 💬 Trò chuyện: {sessions[first_id]['name']}", "ℹ️ *Chưa có Sandbox ID*", [],
                "*(Chưa kích hoạt Kỹ năng nào trong phiên này)*", gr.update(choices=[]), "🌐 **Sandbox hiện tại:** *(Chưa kết nối)*"
            )
        del sessions[cur_id]
        new_cur_id = list(sessions.keys())[0]
        name = sessions[new_cur_id]["name"]
        choices = [s["name"] for s in sessions.values()]
        skills_dict = sessions[new_cur_id].get("skills", {})
        skills_md = render_active_skills_markdown(skills_dict)
        skill_choices = list(skills_dict.keys())
        active_env = get_current_env_id(new_cur_id, sessions)
        env_txt = f"🌐 **Sandbox ID:** `{active_env}`" if active_env else "ℹ️ *Chưa có Sandbox ID*"
        sb_badge = f"🌐 **Sandbox hiện tại:** `{active_env}`" if active_env else "🌐 **Sandbox hiện tại:** *(Chưa kết nối)*"
        return sessions, new_cur_id, gr.update(choices=choices, value=name), f"### 💬 Trò chuyện: {name}", env_txt, sessions[new_cur_id]["history"], skills_md, gr.update(choices=skill_choices, value=skill_choices[0] if skill_choices else None), sb_badge

    new_session_btn.click(
        on_new_session, [sessions_state, current_session_id],
        [sessions_state, current_session_id, session_dropdown, session_title_md, session_env_info, chatbot, system_instruction_input, active_skills_display, remove_skill_dropdown, current_sandbox_display]
    )
    session_dropdown.change(
        on_switch_session, [session_dropdown, sessions_state, current_session_id],
        [current_session_id, session_title_md, session_env_info, chatbot, system_instruction_input, active_skills_display, remove_skill_dropdown, current_sandbox_display]
    )
    delete_session_btn.click(
        on_delete_session, [sessions_state, current_session_id],
        [sessions_state, current_session_id, session_dropdown, session_title_md, session_env_info, chatbot, active_skills_display, remove_skill_dropdown, current_sandbox_display]
    )

    # File Explorer Events
    refresh_files_btn.click(
        list_sandbox_files,
        inputs=[api_key_input, current_session_id, sessions_state],
        outputs=[sandbox_file_choice, sandbox_files_md]
    )
    download_to_colab_btn.click(
        download_file_from_sandbox,
        inputs=[api_key_input, current_session_id, sandbox_file_choice, custom_download_input, sessions_state],
        outputs=[file_action_status]
    )
    upload_to_sandbox_btn.click(
        upload_file_to_sandbox,
        inputs=[api_key_input, current_session_id, upload_file_widget, colab_file_path, sandbox_dest_name, sessions_state],
        outputs=[file_action_status]
    ).then(
        list_sandbox_files,
        inputs=[api_key_input, current_session_id, sessions_state],
        outputs=[sandbox_file_choice, sandbox_files_md]
    )

    # --- Xử lý Sao lưu & Phục hồi Phiên ---
    def handle_save_backup(sessions):
        return save_sessions_backup(sessions)

    def handle_load_backup(sessions, cur_id):
        loaded_data, first_id, choices, msg = load_sessions_backup()
        if not loaded_data:
            return sessions, cur_id, gr.update(), msg, [], "*(Chưa kích hoạt Kỹ năng nào)*", gr.update()
        first_skills = loaded_data[first_id].get("skills", {})
        skills_md = render_active_skills_markdown(first_skills)
        skill_choices = list(first_skills.keys())
        return loaded_data, first_id, gr.update(choices=choices, value=choices[0]), msg, loaded_data[first_id]["history"], skills_md, gr.update(choices=skill_choices, value=skill_choices[0] if skill_choices else None)

    def handle_export_markdown(sessions, cur_id):
        return export_session_markdown(sessions, cur_id)

    # Persistence Events
    save_backup_btn.click(handle_save_backup, inputs=[sessions_state], outputs=[backup_status])
    load_backup_btn.click(
        handle_load_backup, inputs=[sessions_state, current_session_id],
        outputs=[sessions_state, current_session_id, session_dropdown, backup_status, chatbot, active_skills_display, remove_skill_dropdown]
    )
    export_md_btn.click(handle_export_markdown, inputs=[sessions_state, current_session_id], outputs=[backup_status])

    # Clear chat
    clear_btn.click(lambda sess, cid: (sess, {**sess, cid: {**sess[cid], 'history': []}}[cid]['history']), [sessions_state, current_session_id], [sessions_state, chatbot])

    # --- Xử lý tin nhắn & Đính kèm TẤT CẢ các loại tệp (Ảnh, PDF, CSV, Code, ZIP, TXT...) ---
    def user_msg(user_message, history, sessions, cur_id):
        if isinstance(user_message, dict):
            text = str(user_message.get("text", "")).strip()
            files = user_message.get("files", []) or []
        else:
            text = str(user_message).strip()
            files = []

        history = list(history or [])
        image_previews = []
        file_previews = []
        images_data = []
        all_files_data = []

        for f_item in files:
            f_path = f_item if isinstance(f_item, str) else (f_item.get("path") if isinstance(f_item, dict) else "")
            if not f_path or not os.path.exists(f_path):
                continue

            filename = os.path.basename(f_path)
            ext = os.path.splitext(f_path)[1].lower()
            size = os.path.getsize(f_path)
            size_kb = size / 1024

            try:
                with open(f_path, "rb") as bf:
                    raw_bytes = bf.read()
                    b64 = base64.b64encode(raw_bytes).decode("utf-8")
            except Exception:
                continue

            # Phân loại hình ảnh vs tệp tin thông thường
            if ext in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"):
                mime = "image/png"
                if ext in (".jpg", ".jpeg"):
                    mime = "image/jpeg"
                elif ext == ".webp":
                    mime = "image/webp"
                elif ext == ".gif":
                    mime = "image/gif"

                images_data.append({
                    "filename": filename,
                    "mime": mime,
                    "data": b64,
                    "bytes": raw_bytes,
                    "size": size
                })
                image_previews.append(f'<img src="data:{mime};base64,{b64}" style="max-width: 320px; border-radius: 8px; margin-bottom: 6px;" /><br>*{filename} ({size_kb:.1f} KB)*')
            else:
                mime = mimetypes.guess_type(f_path)[0] or "application/octet-stream"
                file_previews.append(f'📎 **[Tệp đính kèm]** `{filename}` *({size_kb:.1f} KB)*')

            all_files_data.append({
                "filename": filename,
                "mime": mime,
                "data": b64,
                "bytes": raw_bytes,
                "size": size
            })

        display_parts = []
        if image_previews:
            display_parts.append("<br>".join(image_previews))
        if file_previews:
            display_parts.append("<br>".join(file_previews))
        if text:
            display_parts.append(text)
        elif not image_previews and not file_previews:
            display_parts.append("*(Tin nhắn trống)*")

        display_content = "<br><br>".join(display_parts)
        new_history = history + [{"role": "user", "content": display_content}]

        # Lưu trạng thái tệp và câu hỏi vào phiên
        sessions[cur_id]["history"] = new_history
        sessions[cur_id]["pending_images"] = images_data
        sessions[cur_id]["pending_files"] = all_files_data
        sessions[cur_id]["pending_text"] = text

        return {"text": "", "files": []}, new_history, sessions

    def bot_msg(history, sessions, cur_id, api_key, agent_choice, custom_agent_text, sys_prompt):
        if not history:
            return
        active_key = api_key.strip() or colab_api_key or os.environ.get("GEMINI_API_KEY", "")

        if not active_key:
            history.append({"role": "assistant", "content": "⚠️ **Chưa có Gemini API Key**: Vui lòng nhập Key vào mục Cấu hình hoặc lưu trong Colab Secrets."})
            sessions[cur_id]["history"] = history
            yield history, sessions, "⚠️ *Chưa có API Key*", "🌐 **Sandbox hiện tại:** *(Chưa có API Key)*"
            return

        chosen_agent = custom_agent_text.strip() if agent_choice == "Tùy chỉnh khác..." and custom_agent_text.strip() else agent_choice

        sessions[cur_id]["system_prompt"] = sys_prompt or ""
        current_skills = sessions[cur_id].get("skills", {})
        pending_text = sessions[cur_id].get("pending_text", "")
        pending_images = sessions[cur_id].get("pending_images", [])
        pending_files = sessions[cur_id].get("pending_files", [])

        # Xây dựng thông báo về các tệp đính kèm để Agent biết rõ trong Sandbox
        file_notices = []
        extra_sources = []
        for pf in pending_files:
            file_notices.append(f"- `{pf['filename']}` ({pf['size']:,} bytes)")
            extra_sources.append({
                "type": "inline",
                "target": pf["filename"],
                "content": pf["data"],
                "encoding": "base64"
            })

        effective_prompt_text = pending_text
        if file_notices:
            attached_summary = "📁 **[Các tệp đã được đính kèm vào thư mục Sandbox hiện tại]:**\n" + "\n".join(file_notices) + "\n\n"
            effective_prompt_text = attached_summary + (pending_text or "Hãy xem các tệp đính kèm trên và giúp tôi xử lý theo yêu cầu.")

        # Xây dựng input cho Google GenAI Interactions API (Hỗ trợ Multimodal Text + Images)
        if pending_images:
            contents = []
            if effective_prompt_text:
                contents.append({"type": "text", "text": effective_prompt_text})
            for img in pending_images:
                contents.append({
                    "type": "image",
                    "mime_type": img["mime"],
                    "data": img["data"]
                })
            agent_input = contents
        else:
            agent_input = effective_prompt_text or "Hello"

        files_info_str = f" [Đính kèm {len(pending_files)} tệp]" if pending_files else ""
        skills_count = len(current_skills)
        if skills_count > 0:
            files_info_str += f" với {skills_count} Kỹ năng"

        history.append({"role": "assistant", "content": f"⏳ *Agent (`{chosen_agent}`){files_info_str} đang xử lý và thực thi trên Cloud Sandbox...*"})
        yield history, sessions, f"⏳ *Đang kết nối siêu máy chủ Google Cloud ({chosen_agent})...*", gr.update()

        # Dọn dẹp trạng thái pending
        sessions[cur_id]["pending_images"] = []
        sessions[cur_id]["pending_files"] = []
        sessions[cur_id]["pending_text"] = ""

        try:
            existing_env = sessions[cur_id].get("env_id")
            if cur_id not in active_sessions_agents or active_sessions_agents[cur_id].api_key != active_key or active_sessions_agents[cur_id].agent != chosen_agent:
                active_sessions_agents[cur_id] = ManagedAgentSession(
                    api_key=active_key,
                    agent=chosen_agent,
                    system_instruction=sys_prompt,
                    skills=current_skills,
                    env_id=existing_env
                )
            elif existing_env and active_sessions_agents[cur_id].env_id != existing_env:
                active_sessions_agents[cur_id].env_id = existing_env

            agent_sess = active_sessions_agents[cur_id]

            # Nếu Sandbox đã đang chạy và có tệp mới, đẩy trực tiếp tệp vào Sandbox
            if agent_sess.env_id and pending_files:
                client_temp = genai.Client(api_key=active_key)
                for pf in pending_files:
                    try:
                        client_temp.environments.files.upload(
                            environment=agent_sess.env_id,
                            path=pf["filename"],
                            file=pf["bytes"]
                        )
                    except Exception:
                        pass

            # Gửi yêu cầu tới Agent (Hỗ trợ Self-Healing tự tạo Sandbox mới nếu Sandbox cũ bị 404/Expired)
            interaction = agent_sess.ask(agent_input, system_instruction=sys_prompt, skills=current_skills, extra_sources=extra_sources)

            # Cập nhật Sandbox ID thực tế sau khi thực thi
            sessions[cur_id]["env_id"] = agent_sess.env_id

            steps_markdown = format_interaction_steps(interaction)
            final_output = interaction.output_text or "*(Đã hoàn thành tác vụ)*"

            auto_notice = ""
            if agent_sess.auto_recreated:
                old_id_str = f"`{agent_sess.old_expired_id}`" if agent_sess.old_expired_id else "cũ"
                auto_notice = f"> 💡 **Tự động phục hồi:** Sandbox {old_id_str} đã hết hạn trên Google Cloud. Hệ thống đã tự động cấp phát Sandbox mới (`{agent_sess.env_id}`) để câu hỏi của bạn được xử lý liền mạch mà không gặp lỗi!\n\n"

            final_reply = f"{auto_notice}{steps_markdown}{final_output}" if steps_markdown else f"{auto_notice}{final_output}"

            history[-1]["content"] = final_reply
            sessions[cur_id]["history"] = history

            env_info = f"🌐 **Sandbox ID:** `{agent_sess.env_id}` (Lượt #{agent_sess.step} | Agent: `{chosen_agent}` | Skills: {len(current_skills)})"
            sb_badge = f"🌐 **Sandbox hiện tại:** `{agent_sess.env_id}`"
            yield history, sessions, env_info, sb_badge

        except Exception as e:
            err_str = str(e)
            if "429" in err_str:
                history[-1]["content"] = "⚠️ **Hạn mức tài khoản bị giới hạn (HTTP 429)**: Vui lòng đợi 30 giây rồi thử lại, hoặc mở phần **Quản lý Sandbox** để xóa bớt Sandbox."
            elif "503" in err_str:
                history[-1]["content"] = "⚠️ **Máy chủ Google tạm bận (HTTP 503)**: Đang có lượng truy cập cao, bạn vui lòng gửi lại sau vài giây."
            else:
                history[-1]["content"] = f"❌ **Lỗi thực thi**: {err_str}"
            sessions[cur_id]["history"] = history
            yield history, sessions, "❌ *Lỗi thực thi*", gr.update()

    # Submit Chat
    msg_input.submit(
        user_msg, [msg_input, chatbot, sessions_state, current_session_id],
        [msg_input, chatbot, sessions_state], queue=False
    ).then(
        bot_msg, [chatbot, sessions_state, current_session_id, api_key_input, agent_select, custom_agent_box, system_instruction_input],
        [chatbot, sessions_state, session_env_info, current_sandbox_display]
    )

    submit_btn.click(
        user_msg, [msg_input, chatbot, sessions_state, current_session_id],
        [msg_input, chatbot, sessions_state], queue=False
    ).then(
        bot_msg, [chatbot, sessions_state, current_session_id, api_key_input, agent_select, custom_agent_box, system_instruction_input],
        [chatbot, sessions_state, session_env_info, current_sandbox_display]
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    share = os.environ.get("GRADIO_SHARE", "True").lower() in ("true", "1")
    demo.queue()
    demo.launch(server_name="0.0.0.0", server_port=port, share=share, debug=True)
