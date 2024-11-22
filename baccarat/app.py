from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# 大路數據存儲
roadmap = []

# A M P 點數分配表
card_values = {
    '1': 1, '2': 1, '3': 1,  # A 或 1 的點數為 1
    '4': 2, '5': 2,
    '6': 3, '7': 3, '8': 3,
    '9': 4,
    '10': 0, 'J': 0, 'Q': 0, 'K': 0,
    'A': 1,  # Ace
    'Z': None  # Z 代表未補牌
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/update_roadmap", methods=["POST"])
def update_roadmap():
    data = request.json
    result = data.get("result")  # 莊、閒、和
    roadmap.append({"result": result})
    return jsonify({"message": "大路規則更新成功", "roadmap": roadmap})


@app.route("/calculate_amp", methods=["POST"])
def calculate_amp():
    data = request.json
    cards = data.get("cards")  # 獲取牌組
    if len(cards) != 6:
        return jsonify({"error": "請輸入正確的 6 張牌（格式如：4 7 8 J K Z）。"}), 400

    try:
        converted_cards = [card_values[card.upper()] for card in cards]
    except KeyError:
        return jsonify({"error": "輸入的牌中包含無效的數值！請檢查"}), 400

    # 定義 A M P 計算邏輯
    def calculate_amp_points(cards, third_card):
        total = sum(cards)
        has_multiplier = any(card == 0 for card in cards)  # 是否有 10, J, Q, K
        if third_card is not None:
            total += third_card
            if third_card == 0:
                has_multiplier = True
        return total * 1.5 if has_multiplier else total

    # 計算 A M P
    player_amp = calculate_amp_points(converted_cards[:2], converted_cards[4])
    banker_amp = calculate_amp_points(converted_cards[2:4], converted_cards[5])

    # 計算勝率
    total_amp = player_amp + banker_amp
    player_win_rate = (player_amp / total_amp) * 100 if total_amp > 0 else 0
    banker_win_rate = (banker_amp / total_amp) * 100 if total_amp > 0 else 0
    tie_rate = 100 - (player_win_rate + banker_win_rate)

    # 大路規則權重（使用全部數據）
    total_results = len(roadmap)
    player_roadmap_rate = sum(1 for r in roadmap if r["result"] == "閒") / total_results * 100 if total_results > 0 else 50
    banker_roadmap_rate = sum(1 for r in roadmap if r["result"] == "莊") / total_results * 100 if total_results > 0 else 50
    tie_roadmap_rate = 100 - (player_roadmap_rate + banker_roadmap_rate)

    # 綜合權重
    final_player_rate = (player_win_rate + player_roadmap_rate) / 2
    final_banker_rate = (banker_win_rate + banker_roadmap_rate) / 2
    final_tie_rate = (tie_rate + tie_roadmap_rate) / 2

    return jsonify({
        "player_amp": round(player_amp, 2),
        "banker_amp": round(banker_amp, 2),
        "player_win_rate": round(final_player_rate, 2),
        "banker_win_rate": round(final_banker_rate, 2),
        "tie_rate": round(final_tie_rate, 2),
    })


if __name__ == "__main__":
    app.run(debug=True)
