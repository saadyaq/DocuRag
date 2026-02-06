#The goal is to have a markdown parser for file md files
#Imports

from pathlib import Path

#Access the file
file_path= Path(r"C:\Users\saady\PycharmProjects\DocuRag\src\ingestion\code.md")




class MarkdownLoader:
    def __init__(self,file_path:Path) -> None:
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

    def load(self) -> list[dict]:

        with open(self.file_path, "r", encoding="utf-8") as file:
            file_content = file.read()
        in_code_block = False
        #Pour les docs sans header
        result = [{"title": "", "level": 0, "content": "", "source": str(self.file_path.resolve())}]
        for l in file_content.split("\n"):
            if l.strip().startswith("```"):
                in_code_block = not in_code_block

            if l.startswith("#") and not in_code_block:

                result.append({
                    "title": l.lstrip("#").strip(),
                    "level": len(l.split(" ")[0]),
                    "content": "",
                    "source" : str(self.file_path.resolve()),

                })

            elif len(result) > 0 and l.strip() :
                result[-1]["content"] += l.strip() + "\n"


        return result


if __name__ == "__main__":
    loader = MarkdownLoader(file_path)
    print(loader.load())