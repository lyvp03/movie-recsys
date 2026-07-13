from dotenv import load_dotenv
load_dotenv('../../.env')
from infrastructure.ml.nrc_emotion_extractor import NRCEmotionExtractor

e = NRCEmotionExtractor()
words = ['sad','sadness','romantic','gentle','love','fear','scary','funny',
         'hilarious','tender','warm','joyful','terrifying','horror','family',
         'light','comedy','happy','lonely','beautiful','heartwarming']
for w in words:
    result = e._lexicon.get(w, 'NOT FOUND')
    print(f"  {w}: {result}")

print()
print("Lexicon size:", len(e._lexicon))
print()

# Test various queries
queries = [
    "gentle romantic movie",
    "sad lonely heartbreaking",
    "scary terrifying horror",
    "funny hilarious comedy",
    "warm tender love story",
    "a light gentle romantic film about love",
]
for q in queries:
    v = e.extract(q)
    total = sum(v.to_list())
    print(f"  '{q}' -> sum={total:.2f} top={max(v.to_dict().items(), key=lambda x: x[1]) if total > 0 else 'EMPTY'}")
