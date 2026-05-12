import anthropic
import sqlite3
import json
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tw_stock_list.sqlite3')

client = anthropic.Anthropic()

MAJOR_INDUSTRIES = [
    "交通運輸及航運", "休閒娛樂", "其他", "前瞻科技", "半導體", "印刷電路板",
    "平面顯示器", "建材營造", "數位科技", "文化創意", "水泥", "汽車",
    "油電燃氣", "生技醫療", "石化及塑橡膠", "紡織", "綠色能源", "自動化",
    "被動元件", "觸控面板", "貿易百貨", "軟體服務", "通信網路", "造紙",
    "連接器", "金融", "鋼鐵", "電子商務", "電機機械", "電腦週邊", "食品",
]

_SYSTEM = (
    "你是台灣股市產業分類專家。判斷 NLP 聚類主題是否為「產業/行業主題」（非閒聊、情緒、政治）。\n"
    f"可選大類（只能選一個，或 null）：{json.dumps(MAJOR_INDUSTRIES, ensure_ascii=False)}"
)


def classify_topic(name: str) -> dict:
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        system=_SYSTEM,
        messages=[{
            "role": "user",
            "content": (
                f'主題名稱：「{name}」\n'
                '僅回覆 JSON：{"is_industry": true/false, "major_industry": "xxx" or null}'
            ),
        }],
    )
    return json.loads(resp.content[0].text)


def run() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    topics = conn.execute(
        '''SELECT t.id, t.name FROM nlp_topics t
           LEFT JOIN nlp_topic_industry_map m ON t.id = m.topic_id
           WHERE t.level = 'fine' AND m.topic_id IS NULL'''
    ).fetchall()

    now = datetime.now(timezone.utc).isoformat()
    for topic in topics:
        result = classify_topic(topic['name'])
        conn.execute(
            'INSERT OR REPLACE INTO nlp_topic_industry_map '
            '(topic_id, is_industry, major_industry, classified_at) VALUES (?, ?, ?, ?)',
            (
                topic['id'],
                1 if result.get('is_industry') else 0,
                result.get('major_industry'),
                now,
            ),
        )
        conn.commit()
        label = '產業' if result.get('is_industry') else '雜訊'
        mapped = result.get('major_industry') or ''
        print(f"  {topic['name']} → {label} {mapped}")

    conn.close()


if __name__ == '__main__':
    run()
