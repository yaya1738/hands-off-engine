import os
import openai
import logging
import time
from dotenv import load_dotenv


class ChatGPTProvider:
    def __init__(self, model_name: str = None, max_retries: int = 3, backoff_factor: float = 1.5):
        """
        ChatGPTProvider uses OpenAI's ChatCompletion API to generate a
        response for a given task.

        :param model_name: Optional custom model name (default uses GPT-5.1
                          preview or GPT-4).
        :param max_retries: How many times to retry on error (default 3).
        :param backoff_factor: Multiplier for exponential backoff between
                              retries.
        """
        # Load API key from environment or .env file
        load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"), override=True)
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OpenAI API key not found. Set OPENAI_API_KEY in "
                             "environment or .env file.")
        openai.api_key = api_key

        # Allow overriding model via env or parameter
        self.model = model_name or os.getenv("OPENAI_MODEL", "gpt-4-1106-preview")
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

        # Configure a logger for this provider
        self.logger = logging.getLogger(self.__class__.__name__)
        if not self.logger.handlers:  # Avoid duplicate handlers if multiple instances
            logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s",
                              level=logging.INFO)
        self.logger.setLevel(logging.INFO)
        self.logger.info(f"ChatGPTProvider initialized with model={self.model}")

    def _read_context_files(self, context_files):
        """Helper to read and concatenate content from context files."""
        context_text = ""
        for file_path in context_files or []:
            try:
                # Determine absolute path if needed (assuming context_files are repo-relative)
                abs_path = file_path if os.path.isabs(file_path) else \
                          os.path.join(os.getcwd(), file_path)
                with open(abs_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                if content:
                    # Append file content with a header for clarity
                    context_text += f"\n[[FILE: {file_path}]]\n{content}\n"
                    self.logger.info(f"Loaded context file: {file_path} "
                                   f"(size={len(content)} chars)")
            except Exception as e:
                self.logger.error(f"Failed to read context file {file_path}: {e}")
        return context_text

    def run_task(self, task: dict) -> dict:
        """
        Execute the given task using ChatGPT and return a structured result.

        Task format:
          { "provider": "chatgpt", "prompt": "<user prompt>",
            "context_files": ["<path1>", "..."] }
        """
        prompt = task.get("prompt", "")
        context_files = task.get("context_files", [])

        # Build the message payload for ChatGPT
        messages = []

        # If there is context, include it as a system message
        if context_files:
            context_content = self._read_context_files(context_files)
            if context_content:
                system_msg = "You are ChatGPT, an AI assistant. Use the provided " \
                           "context to answer the user's query.\n"
                system_msg += f"Context from files:{context_content}\nEnd of context.\n"
                messages.append({"role": "system", "content": system_msg})

        # Add the user prompt as the final user message
        messages.append({"role": "user", "content": prompt})

        self.logger.info(f"Sending prompt to ChatGPT (model={self.model}, "
                        f"context_files={len(context_files)})")

        # Call the OpenAI ChatCompletion API with retries
        attempt = 0
        result = {"provider": "chatgpt", "success": False, "content": None, "error": None}

        while attempt < self.max_retries:
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.0  # using deterministic behavior for consistent results
                )
                # Extract assistant response content
                answer = response["choices"][0]["message"]["content"]
                result.update({
                    "success": True,
                    "content": answer,
                    "usage": response.get("usage", {})
                })
                self.logger.info(f"ChatGPT response received (tokens "
                               f"used={result['usage'].get('total_tokens')})")
                break  # successful
            except Exception as e:
                attempt += 1
                self.logger.error(f"ChatGPT API call failed (attempt {attempt}/"
                                f"{self.max_retries}): {e}")
                # If we've exhausted retries, record the error and break
                if attempt >= self.max_retries:
                    result["error"] = str(e)
                    self.logger.error("Max retries reached. Giving up on this task.")
                else:
                    # Exponential backoff before next retry
                    sleep_time = self.backoff_factor ** attempt
                    self.logger.info(f"Retrying after {sleep_time:.1f}s...")
                    time.sleep(sleep_time)

        return result
