import sys, os, json
from pathlib import Path
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from content.content_generator import generate_title, generate_summary
from content.post_generator import create_post
from database.user_service import get_user_settings

file_path = "data/articles.json"

def run_pipeline_2(choice, user_id):
    settings = get_user_settings(user_id)
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    data = []
    try:
        with open(file_path, 'r', encoding= "utf-8") as file:
            data = json.load(file)
    except Exception as e:
        print(f"There is problem with opening the file! {e}")
        sys.exit(1)

    final_content = [generate_title(data[choice - 1], settings), generate_summary(data[choice - 1], settings)]
    summary_path = Path("output") / f"{now}" / "description.txt"
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    with open(summary_path, "w", encoding="utf-8") as file:
        file.write(final_content[1])
        print("description saved!")

    image_path = summary_path.parent / "post.jpg"
    data[choice - 1]['title']= final_content[0]
    img = create_post(data[choice-1], settings)

    img.save(image_path)
    print("image saved!")


if __name__ == "__main__":
    run_pipeline_2()
    

