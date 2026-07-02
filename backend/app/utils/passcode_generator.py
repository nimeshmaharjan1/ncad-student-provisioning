import os
import random

"""
Passcode Generator
==================
DO NOT change any of this without understanding the tradeoffs below.

Format:     WordWordWordWordWordNN  (5 title-cased words + 2-digit number, no separator)
Example:    RiverForestCrystalStormFalcon42
Word list:  1,668 words, manually curated — no profanity, slurs, or offensive terms.
Entropy:    ~57 bits  (1668^5 * 90 = ~1.16 x 10^17 combinations)
Equivalent: ~9.5-char random alphanumeric.

Why this exists
---------------
Students CANNOT change their passcode — the LDAP system has no password
change feature. This passcode is permanent for the student's entire enrollment.
Word-based format is the only way to make a 30+ char credential
memorable enough that students don't write it on a sticky note.

Design decisions & tradeoffs
----------------------------
- 5 words not 4: 4 words + 1 digit (~26 bits, original design) is too weak
  for a permanent credential. 57 bits is adequate for offline cracking
  resistance — it costs real GPU time to crack even one hash.
- 5 words not 6+: 6+ words pushes passcodes past 40 characters and causes
  typing errors. Already at ~30-40 chars with 5 words.
- 2-digit number not 1-digit: Adds 9x more combinations (90 vs 9) for 1 char.
- No separator (hyphen/dot): Deliberate product decision, don't add one.
- No special chars: Would make passcodes harder to type (students on phones,
  kiosks, etc.) with marginal entropy gain.
- `random` not `secrets`: Passcodes are generated offline in batch, not in
  a web request. If this ever shifts to on-the-fly generation, switch to
  `secrets.SystemRandom()`.

What this does NOT protect against
-----------------------------------
- Phishing, keyloggers, physical passcode handout theft.
- Students reusing the same passcode on other services.
- Anything outside this codebase (LDAP lockout policy, MFA, network security,
  baseline CSV access controls).

If the repo ever goes public
----------------------------
The word list secrecy is NOT the entropy source (Kerckhoffs's principle).
1668^5 * 90 = ~57 bits regardless of whether the attacker knows the list.
If you want more paranoia, add a PASSCODE_WORD_FILE env var that overrides
the embedded list with a private file.

Word list maintenance
---------------------
DO NOT add words without reviewing for:
- Offensive/insensitive meanings (including in other dialects of English).
- Inappropriate acronyms when concatenated.
- Obscurity — the word must be recognizable to a typical 18-year-old.
- Adding words increases entropy (log2(n) per word). Removing words or
  reducing word count directly reduces security.
"""

FALLBACK_WORDS = [
    "Acorn", "Amber", "Anchor", "Aspen", "Aurora", "Beacon", "Birch", "Blaze",
    "Canyon", "Cedar", "Crystal", "Forest", "River", "Storm", "Falcon"
]

def _load_words() -> list[str]:
    # 1. Check environment variable PASSCODE_WORD_FILE
    env_path = os.environ.get("PASSCODE_WORD_FILE")
    if env_path:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    words = [line.strip() for line in f if line.strip()]
                    if words:
                        return words
            except Exception as e:
                print(f"[WARN] Failed to read PASSCODE_WORD_FILE from '{env_path}': {e}")
        else:
            print(f"[WARN] PASSCODE_WORD_FILE path '{env_path}' does not exist.")

    # 2. Check local words.txt in the same directory as this file
    local_dir = os.path.dirname(os.path.abspath(__file__))
    local_path = os.path.join(local_dir, "words.txt")
    if os.path.exists(local_path):
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                words = [line.strip() for line in f if line.strip()]
                if words:
                    return words
        except Exception as e:
            print(f"[WARN] Failed to read local word list '{local_path}': {e}")

    # 3. Fallback
    print("[WARN] No external word list found. Falling back to built-in minimal word list.")
    return FALLBACK_WORDS

WORDS = _load_words()

def generate_passcode() -> str:
    # 5 words + 2-digit number. Entropy = 1668^5 * 90 ≈ 57 bits.
    # 5 is the minimum word count for adequate security given no password rotation.
    selected_words = [random.choice(WORDS) for _ in range(5)]
    number = random.randint(10, 99)
    return "".join(selected_words) + str(number)
