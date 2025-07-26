from util.construct_email import send_email
from arxiv_daily import ArxivDaily
import argparse
import os



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Arxiv Daily")
    parser.add_argument("--categories", nargs="+", help="categories", required=True)
    parser.add_argument("--max_paper_num", type=int, help="max_paper_num", default=60)
    parser.add_argument(
        "--max_entries", type=int, help="max_entries to get from arxiv", default=100
    )
    parser.add_argument("--provider", type=str, help="provider", required=True)
    parser.add_argument("--model", type=str, help="model", required=None)
    parser.add_argument(
        "--save", action="store_true", help="Save the email content to a file."
    )
    parser.add_argument("--save_dir", type=str, default="./arxiv_history")

    parser.add_argument("--base_url", type=str, help="base_url", default=None)
    parser.add_argument("--api_key", type=str, help="api_key", default=None)

    parser.add_argument(
        "--description",
        type=str,
        help="Path to the file that describes your interested research area.",
        default="description.txt",
    )

    parser.add_argument("--smtp_server", type=str, help="SMTP server")
    parser.add_argument("--smtp_port", type=int, help="SMTP port")
    parser.add_argument("--sender", type=str, help="Sender email address")
    parser.add_argument("--receiver", type=str, help="Receiver email address")
    parser.add_argument("--sender_password", type=str, help="Sender email password")
    parser.add_argument("--temperature", type=float, help="Temperature", default=0.7)

    parser.add_argument("--num_workers", type=int, help="Number of workers", default=4)
    parser.add_argument(
        "--title", type=str, help="Title of the email", default="Daily arXiv"
    )
    parser.add_argument("--language", type=str, help="Language for email content", default="zh")

    args = parser.parse_args()

    if not (args.provider == "Ollama" or args.provider == "ollama"):
        assert args.base_url is not None, (
            "base_url is required for SiliconFlow and OpenAI"
        )
        assert args.api_key is not None, (
            "api_key is required for SiliconFlow and OpenAI"
        )

    with open(args.description, "r") as f:
        args.description = f.read()

    # Test LLM availability
    if args.provider == "Ollama" or args.provider == "ollama":
        from llm.Ollama import Ollama

        try:
            model = Ollama(args.model)
            model.inference("Hello, who are you?")
        except Exception as e:
            print(e)
            assert False, "Model not initialized successfully."
    elif (
        args.provider == "OpenAI"
        or args.provider == "openai"
        or args.provider == "SiliconFlow"
    ):
        from llm.GPT import GPT

        try:
            model = GPT(args.model, args.base_url, args.api_key)
            model.inference("Hello, who are you?")
        except Exception as e:
            print(e)
            assert False, "Model not initialized successfully."
    else:
        assert False, "Model not supported."

    if args.save:
        os.makedirs(args.save_dir, exist_ok=True)
    else:
        args.save_dir = None

    arxiv_daily = ArxivDaily(
        args.categories,
        args.max_entries,
        args.max_paper_num,
        args.provider,
        args.model,
        args.base_url,
        args.api_key,
        args.description,
        args.num_workers,
        args.temperature,
        save_dir=args.save_dir,
        language=args.language,
    )

    arxiv_daily.send_email(
        args.sender,
        args.receiver,
        args.sender_password,
        args.smtp_server,
        args.smtp_port,
        args.title,
    )
