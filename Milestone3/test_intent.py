from backend.intent_parser import parse_user_intent

queries = [
    "How many points did Salah score in 2021-22?",
    "Compare Haaland and Kane",
    "Who are the best defenders?",
    "Is Saka injured?",
    "Hello, how are you?"
]

print("🧠 Testing Intent Parser...\n")

for q in queries:
    result = parse_user_intent(q)
    print(f"🗣️  Query: '{q}'")
    print(f"🔍 Result: {result}\n")