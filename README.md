# 🗼 Restricted Tower of Hanoi — Interactive Game

> **DAA Assignment #4 | Project Part II**
> Bahria University, Islamabad | BSCS-5A, Spring 2026
> **Muhammad Ahmad** | Enrollment: 01-134241-024

---

## 📌 What is the Restricted Tower of Hanoi?

The **Restricted Tower of Hanoi** is a variant of the classic puzzle where **direct moves between the Source (S) and Destination (D) pegs are forbidden**. Every disk must pass through the Middle (M) peg.

| Property | Standard Hanoi | Restricted Hanoi |
|---|---|---|
| Allowed moves | S↔M, S↔D, M↔D | **S↔M and M↔D only** |
| Min moves formula | 2ⁿ − 1 | **3ⁿ − 1** |
| Algorithm | Divide & Conquer | Divide & Conquer |
| Time Complexity | O(2ⁿ) | **O(3ⁿ)** |

---

## 🎮 Features

- 🎯 **4 Difficulty Levels** — 3, 4, 5, and 6 disks (26 to 728 optimal moves)
- 🖱️ **Drag-and-Drop** gameplay — pick up and place disks intuitively
- 💡 **Hint System** — highlights the optimal next move with a gold glow
- ↩️ **Undo Button** — reverse any move at any time
- ▶️ **Auto-Solve Mode** — watch the algorithm solve the puzzle step by step
- 🔊 **Sound Effects** — distinct tones for moves, errors, hints, and victory
- ⏸️ **Pause / Resume** — pause the timer mid-game
- 🏆 **Leaderboard** — best scores saved per difficulty level (JSON persistence)
- 📊 **Optimal Move Counter** — tracks how many extra moves you used vs the optimal

---

## 🚀 How to Run

### Prerequisites
```bash
pip install pillow
# Optional (for sound on Linux/Mac):
pip install pygame numpy
```

### Run the game
```bash
python Restricted_Tower_of_Hanoi_Enhanced.py
```

> **Note:** Background images (`background.png`, `background1.png`, `background2.png`) are optional. The game runs fine without them using a default blue background.

---

## 📁 Project Structure

```
Restricted-Tower-of-Hanoi/
│
├── Restricted_Tower_of_Hanoi_Enhanced.py   # Main game file (enhanced version)
├── Restricted_Tower_of_Hanoi.py            # Original version
├── records.json                            # Auto-generated high score file
├── requirements.txt                        # Python dependencies
├── background.png                          # (optional) Main menu background
├── background1.png                         # (optional) Difficulty menu background
├── background2.png                         # (optional) Game canvas background
└── README.md
```

---

## 🧠 Algorithm

The Restricted Tower of Hanoi uses a **recursive Divide & Conquer** approach:

```
To move n disks from Source → Destination (via Middle only):
  1. Move top (n-1) disks:  Source → Destination  (using Middle)
  2. Move disk n:           Source → Middle
  3. Move top (n-1) disks:  Destination → Source   (using Middle)
  4. Move disk n:           Middle → Destination
  5. Move top (n-1) disks:  Source → Destination  (using Middle)
```

**Recurrence:** `T(n) = 3·T(n−1) + 2`, solved as `T(n) = 3ⁿ − 1`

---

## 📸 Screenshots

| Main Menu | Gameplay | Victory Screen |
|---|---|---|
| *(add screenshot)* | *(add screenshot)* | *(add screenshot)* |

---

## 🛠️ Built With

- **Python 3.x**
- **tkinter** — GUI and canvas drawing
- **Pillow (PIL)** — background image loading and resizing
- **json** — persistent high score storage
- **pygame / winsound** — cross-platform sound effects

---

## 📝 License

This project was developed as part of a university assignment. Free to use for educational purposes.
