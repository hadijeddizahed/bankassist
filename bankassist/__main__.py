import argparse
import json
from pathlib import Path
from bankassist.core import BankAssistant, Document, ExtractiveGenerator, KeywordRetriever


def main():
    parser = argparse.ArgumentParser(description='Fictional banking policy retrieval baseline')
    parser.add_argument('question')
    args = parser.parse_args()
    path = Path(__file__).resolve().parents[1] / 'data' / 'policies.json'
    documents = [Document(**row) for row in json.loads(path.read_text())]
    assistant = BankAssistant(KeywordRetriever(documents), ExtractiveGenerator())
    try:
        answer = assistant.answer(args.question)
    except ValueError as error:
        parser.error(str(error))
    print(answer.text)
    print('Context sources:', ', '.join(answer.sources) or 'none')


if __name__ == '__main__':
    main()
