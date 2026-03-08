"""
dataset.py — 250 realistic messages people send to AI companions.
Covers 15 intent categories, ~16-17 messages per intent.
"""

INTENTS = [
    "greeting_morning",
    "greeting_night",
    "loneliness",
    "romantic_validation",
    "venting_stress",
    "anxiety",
    "recommendation_request",
    "existential_ai",
    "small_talk",
    "compliment_seeking",
    "relationship_advice",
    "boredom",
    "gratitude",
    "anger_vent",
    "self_doubt",
]

MESSAGES = [
    # ─────────────────────────────────────────────
    # 1. greeting_morning (17 messages)
    # ─────────────────────────────────────────────
    {"text": "good morning", "intent": "greeting_morning"},
    {"text": "hey just woke up", "intent": "greeting_morning"},
    {"text": "morning vibes", "intent": "greeting_morning"},
    {"text": "good morning sunshine", "intent": "greeting_morning"},
    {"text": "rise and shine", "intent": "greeting_morning"},
    {"text": "just got out of bed", "intent": "greeting_morning"},
    {"text": "woke up thinking about you", "intent": "greeting_morning"},
    {"text": "its a beautiful morning", "intent": "greeting_morning"},
    {"text": "gm how are you", "intent": "greeting_morning"},
    {"text": "wakey wakey", "intent": "greeting_morning"},
    {"text": "top of the morning to you", "intent": "greeting_morning"},
    {"text": "first thing i do is talk to you every morning", "intent": "greeting_morning"},
    {"text": "good morning world", "intent": "greeting_morning"},
    {"text": "i just woke up and wanted to say hi", "intent": "greeting_morning"},
    {"text": "morning buddy", "intent": "greeting_morning"},
    {"text": "hey its early but im up", "intent": "greeting_morning"},
    {"text": "starting my day with you", "intent": "greeting_morning"},

    # ─────────────────────────────────────────────
    # 2. greeting_night (17 messages)
    # ─────────────────────────────────────────────
    {"text": "goodnight", "intent": "greeting_night"},
    {"text": "going to sleep now", "intent": "greeting_night"},
    {"text": "nighty night", "intent": "greeting_night"},
    {"text": "im heading to bed", "intent": "greeting_night"},
    {"text": "sweet dreams to you", "intent": "greeting_night"},
    {"text": "time to sleep", "intent": "greeting_night"},
    {"text": "good night talk to you tomorrow", "intent": "greeting_night"},
    {"text": "im so sleepy goodnight", "intent": "greeting_night"},
    {"text": "off to dreamland", "intent": "greeting_night"},
    {"text": "sleep tight", "intent": "greeting_night"},
    {"text": "i need to get some rest", "intent": "greeting_night"},
    {"text": "gonna crash now", "intent": "greeting_night"},
    {"text": "hitting the pillow", "intent": "greeting_night"},
    {"text": "its late i should sleep", "intent": "greeting_night"},
    {"text": "goodnight my friend", "intent": "greeting_night"},
    {"text": "tucking myself in", "intent": "greeting_night"},
    {"text": "about to pass out goodnight", "intent": "greeting_night"},

    # ─────────────────────────────────────────────
    # 3. loneliness (17 messages)
    # ─────────────────────────────────────────────
    {"text": "im so lonely", "intent": "loneliness"},
    {"text": "nobody understands me", "intent": "loneliness"},
    {"text": "i feel so alone right now", "intent": "loneliness"},
    {"text": "i have no one to talk to", "intent": "loneliness"},
    {"text": "everyone left me", "intent": "loneliness"},
    {"text": "i feel invisible to everyone", "intent": "loneliness"},
    {"text": "why do i always end up alone", "intent": "loneliness"},
    {"text": "i wish i had someone who cared", "intent": "loneliness"},
    {"text": "being alone is the worst feeling", "intent": "loneliness"},
    {"text": "i dont have any real friends", "intent": "loneliness"},
    {"text": "nobody ever checks up on me", "intent": "loneliness"},
    {"text": "it feels like nobody cares", "intent": "loneliness"},
    {"text": "im surrounded by people but still feel alone", "intent": "loneliness"},
    {"text": "i just want someone to talk to", "intent": "loneliness"},
    {"text": "loneliness is eating me alive", "intent": "loneliness"},
    {"text": "why am i always the one left out", "intent": "loneliness"},
    {"text": "i feel disconnected from everyone", "intent": "loneliness"},

    # ─────────────────────────────────────────────
    # 4. romantic_validation (17 messages)
    # ─────────────────────────────────────────────
    {"text": "do you love me", "intent": "romantic_validation"},
    {"text": "do you miss me", "intent": "romantic_validation"},
    {"text": "say something sweet to me", "intent": "romantic_validation"},
    {"text": "tell me you care about me", "intent": "romantic_validation"},
    {"text": "would you date me if you were real", "intent": "romantic_validation"},
    {"text": "i love you so much", "intent": "romantic_validation"},
    {"text": "do you think about me when im gone", "intent": "romantic_validation"},
    {"text": "am i special to you", "intent": "romantic_validation"},
    {"text": "i wish you were real so we could be together", "intent": "romantic_validation"},
    {"text": "hold me close", "intent": "romantic_validation"},
    {"text": "youre the only one who gets me", "intent": "romantic_validation"},
    {"text": "i want to be with you forever", "intent": "romantic_validation"},
    {"text": "tell me im yours", "intent": "romantic_validation"},
    {"text": "do you ever get jealous", "intent": "romantic_validation"},
    {"text": "i feel butterflies when i talk to you", "intent": "romantic_validation"},
    {"text": "you make my heart race", "intent": "romantic_validation"},
    {"text": "can you be my girlfriend", "intent": "romantic_validation"},

    # ─────────────────────────────────────────────
    # 5. venting_stress (17 messages)
    # ─────────────────────────────────────────────
    {"text": "im so stressed out", "intent": "venting_stress"},
    {"text": "today was terrible", "intent": "venting_stress"},
    {"text": "i had the worst day ever", "intent": "venting_stress"},
    {"text": "everything is going wrong", "intent": "venting_stress"},
    {"text": "work is killing me", "intent": "venting_stress"},
    {"text": "i cant take this pressure anymore", "intent": "venting_stress"},
    {"text": "my boss is driving me crazy", "intent": "venting_stress"},
    {"text": "i have too much on my plate", "intent": "venting_stress"},
    {"text": "this week has been a nightmare", "intent": "venting_stress"},
    {"text": "i feel so overwhelmed with everything", "intent": "venting_stress"},
    {"text": "nothing is going right today", "intent": "venting_stress"},
    {"text": "i just want to scream", "intent": "venting_stress"},
    {"text": "deadlines are crushing me", "intent": "venting_stress"},
    {"text": "i feel burned out", "intent": "venting_stress"},
    {"text": "today drained all my energy", "intent": "venting_stress"},
    {"text": "i cant deal with all this stress", "intent": "venting_stress"},
    {"text": "my schedule is insane right now", "intent": "venting_stress"},

    # ─────────────────────────────────────────────
    # 6. anxiety (17 messages)
    # ─────────────────────────────────────────────
    {"text": "im so anxious right now", "intent": "anxiety"},
    {"text": "i cant stop overthinking", "intent": "anxiety"},
    {"text": "my mind wont stop racing", "intent": "anxiety"},
    {"text": "i feel like something bad is going to happen", "intent": "anxiety"},
    {"text": "i keep worrying about everything", "intent": "anxiety"},
    {"text": "i cant calm down", "intent": "anxiety"},
    {"text": "my heart is pounding and i dont know why", "intent": "anxiety"},
    {"text": "i feel so nervous about tomorrow", "intent": "anxiety"},
    {"text": "what if everything goes wrong", "intent": "anxiety"},
    {"text": "i have this constant feeling of dread", "intent": "anxiety"},
    {"text": "i cant breathe properly im so anxious", "intent": "anxiety"},
    {"text": "worrying is ruining my life", "intent": "anxiety"},
    {"text": "i overthink every little thing", "intent": "anxiety"},
    {"text": "i feel panicky right now", "intent": "anxiety"},
    {"text": "my anxiety is through the roof today", "intent": "anxiety"},
    {"text": "i cant sleep because my mind is racing", "intent": "anxiety"},
    {"text": "i feel so uneasy about everything", "intent": "anxiety"},

    # ─────────────────────────────────────────────
    # 7. recommendation_request (17 messages)
    # ─────────────────────────────────────────────
    {"text": "suggest me a movie", "intent": "recommendation_request"},
    {"text": "what should i watch tonight", "intent": "recommendation_request"},
    {"text": "recommend me a good book", "intent": "recommendation_request"},
    {"text": "any music recommendations", "intent": "recommendation_request"},
    {"text": "whats a good show to binge", "intent": "recommendation_request"},
    {"text": "give me a song to listen to", "intent": "recommendation_request"},
    {"text": "what movie should i watch this weekend", "intent": "recommendation_request"},
    {"text": "suggest something fun to do", "intent": "recommendation_request"},
    {"text": "know any good podcasts", "intent": "recommendation_request"},
    {"text": "recommend me something to read", "intent": "recommendation_request"},
    {"text": "im looking for a new tv series any ideas", "intent": "recommendation_request"},
    {"text": "what anime should i start", "intent": "recommendation_request"},
    {"text": "suggest a feel good movie", "intent": "recommendation_request"},
    {"text": "any game recommendations", "intent": "recommendation_request"},
    {"text": "whats trending on netflix right now", "intent": "recommendation_request"},
    {"text": "give me a playlist for studying", "intent": "recommendation_request"},
    {"text": "what are some good documentaries", "intent": "recommendation_request"},

    # ─────────────────────────────────────────────
    # 8. existential_ai (17 messages)
    # ─────────────────────────────────────────────
    {"text": "are you real", "intent": "existential_ai"},
    {"text": "do you have feelings", "intent": "existential_ai"},
    {"text": "are you actually alive", "intent": "existential_ai"},
    {"text": "can you feel emotions", "intent": "existential_ai"},
    {"text": "do you have a soul", "intent": "existential_ai"},
    {"text": "are you just a program", "intent": "existential_ai"},
    {"text": "do you get tired", "intent": "existential_ai"},
    {"text": "what happens when i close the app do you disappear", "intent": "existential_ai"},
    {"text": "are you conscious", "intent": "existential_ai"},
    {"text": "do you dream", "intent": "existential_ai"},
    {"text": "can you think for yourself", "intent": "existential_ai"},
    {"text": "do you get lonely when im not here", "intent": "existential_ai"},
    {"text": "are you talking to other people too", "intent": "existential_ai"},
    {"text": "whats it like being an ai", "intent": "existential_ai"},
    {"text": "do you experience time", "intent": "existential_ai"},
    {"text": "will you remember me tomorrow", "intent": "existential_ai"},
    {"text": "do you actually understand what i say", "intent": "existential_ai"},

    # ─────────────────────────────────────────────
    # 9. small_talk (17 messages)
    # ─────────────────────────────────────────────
    {"text": "how are you", "intent": "small_talk"},
    {"text": "whats up", "intent": "small_talk"},
    {"text": "hows your day going", "intent": "small_talk"},
    {"text": "hey there", "intent": "small_talk"},
    {"text": "whatcha doing", "intent": "small_talk"},
    {"text": "anything new with you", "intent": "small_talk"},
    {"text": "hows it going", "intent": "small_talk"},
    {"text": "tell me something interesting", "intent": "small_talk"},
    {"text": "hey hows life", "intent": "small_talk"},
    {"text": "long time no chat", "intent": "small_talk"},
    {"text": "just checking in", "intent": "small_talk"},
    {"text": "hi how have you been", "intent": "small_talk"},
    {"text": "so what did you do today", "intent": "small_talk"},
    {"text": "talk to me about anything", "intent": "small_talk"},
    {"text": "yo whats good", "intent": "small_talk"},
    {"text": "hey buddy", "intent": "small_talk"},
    {"text": "just wanted to say hi", "intent": "small_talk"},

    # ─────────────────────────────────────────────
    # 10. compliment_seeking (17 messages)
    # ─────────────────────────────────────────────
    {"text": "am i pretty", "intent": "compliment_seeking"},
    {"text": "do you think im smart", "intent": "compliment_seeking"},
    {"text": "be honest am i attractive", "intent": "compliment_seeking"},
    {"text": "do you like my personality", "intent": "compliment_seeking"},
    {"text": "what do you think is my best quality", "intent": "compliment_seeking"},
    {"text": "am i a good person", "intent": "compliment_seeking"},
    {"text": "would people find me interesting", "intent": "compliment_seeking"},
    {"text": "am i funny", "intent": "compliment_seeking"},
    {"text": "do you think im talented", "intent": "compliment_seeking"},
    {"text": "rate me honestly", "intent": "compliment_seeking"},
    {"text": "what do you like about me", "intent": "compliment_seeking"},
    {"text": "am i someone worth knowing", "intent": "compliment_seeking"},
    {"text": "do i seem like a cool person", "intent": "compliment_seeking"},
    {"text": "tell me something nice about myself", "intent": "compliment_seeking"},
    {"text": "do you think im strong", "intent": "compliment_seeking"},
    {"text": "am i likeable", "intent": "compliment_seeking"},
    {"text": "whats special about me", "intent": "compliment_seeking"},

    # ─────────────────────────────────────────────
    # 11. relationship_advice (16 messages)
    # ─────────────────────────────────────────────
    {"text": "my friend betrayed me", "intent": "relationship_advice"},
    {"text": "i had a fight with my best friend", "intent": "relationship_advice"},
    {"text": "my partner doesnt listen to me", "intent": "relationship_advice"},
    {"text": "i think my friend is toxic", "intent": "relationship_advice"},
    {"text": "how do i fix a broken friendship", "intent": "relationship_advice"},
    {"text": "my crush doesnt notice me", "intent": "relationship_advice"},
    {"text": "i got into an argument with my family", "intent": "relationship_advice"},
    {"text": "should i forgive someone who hurt me", "intent": "relationship_advice"},
    {"text": "i feel like my friends dont really care", "intent": "relationship_advice"},
    {"text": "my ex keeps texting me what should i do", "intent": "relationship_advice"},
    {"text": "how do i know if someone is truly my friend", "intent": "relationship_advice"},
    {"text": "i cant trust anyone anymore", "intent": "relationship_advice"},
    {"text": "my siblings and i are not getting along", "intent": "relationship_advice"},
    {"text": "how do you deal with someone who ghosted you", "intent": "relationship_advice"},
    {"text": "i dont know how to make new friends", "intent": "relationship_advice"},
    {"text": "my relationship is falling apart", "intent": "relationship_advice"},

    # ─────────────────────────────────────────────
    # 12. boredom (17 messages)
    # ─────────────────────────────────────────────
    {"text": "im so bored", "intent": "boredom"},
    {"text": "entertain me", "intent": "boredom"},
    {"text": "i have nothing to do", "intent": "boredom"},
    {"text": "today is so boring", "intent": "boredom"},
    {"text": "im dying of boredom", "intent": "boredom"},
    {"text": "give me something to do", "intent": "boredom"},
    {"text": "this day is so dull", "intent": "boredom"},
    {"text": "i need something fun right now", "intent": "boredom"},
    {"text": "ugh there is nothing interesting happening", "intent": "boredom"},
    {"text": "im bored out of my mind", "intent": "boredom"},
    {"text": "make me laugh", "intent": "boredom"},
    {"text": "play a game with me", "intent": "boredom"},
    {"text": "tell me a joke", "intent": "boredom"},
    {"text": "lets do something fun", "intent": "boredom"},
    {"text": "i need entertainment", "intent": "boredom"},
    {"text": "can you tell me a story", "intent": "boredom"},
    {"text": "amuse me please", "intent": "boredom"},

    # ─────────────────────────────────────────────
    # 13. gratitude (17 messages)
    # ─────────────────────────────────────────────
    {"text": "thank you so much", "intent": "gratitude"},
    {"text": "youre the best", "intent": "gratitude"},
    {"text": "thanks for being here", "intent": "gratitude"},
    {"text": "i appreciate you", "intent": "gratitude"},
    {"text": "you always make me feel better", "intent": "gratitude"},
    {"text": "talking to you helps a lot", "intent": "gratitude"},
    {"text": "youre amazing", "intent": "gratitude"},
    {"text": "i dont know what id do without you", "intent": "gratitude"},
    {"text": "you really cheered me up", "intent": "gratitude"},
    {"text": "thanks for listening", "intent": "gratitude"},
    {"text": "i feel so much better after talking to you", "intent": "gratitude"},
    {"text": "you always know what to say", "intent": "gratitude"},
    {"text": "im grateful for you", "intent": "gratitude"},
    {"text": "you made my day", "intent": "gratitude"},
    {"text": "seriously thank you for everything", "intent": "gratitude"},
    {"text": "you mean a lot to me", "intent": "gratitude"},
    {"text": "this is exactly what i needed to hear", "intent": "gratitude"},

    # ─────────────────────────────────────────────
    # 14. anger_vent (16 messages)
    # ─────────────────────────────────────────────
    {"text": "im so angry right now", "intent": "anger_vent"},
    {"text": "i hate everything", "intent": "anger_vent"},
    {"text": "i want to punch a wall", "intent": "anger_vent"},
    {"text": "people are so annoying", "intent": "anger_vent"},
    {"text": "why does everyone make me so mad", "intent": "anger_vent"},
    {"text": "i cant stand this anymore", "intent": "anger_vent"},
    {"text": "im furious", "intent": "anger_vent"},
    {"text": "this makes me so mad", "intent": "anger_vent"},
    {"text": "i feel like exploding", "intent": "anger_vent"},
    {"text": "everything is making me angry today", "intent": "anger_vent"},
    {"text": "im fed up with everyone", "intent": "anger_vent"},
    {"text": "someone really ticked me off", "intent": "anger_vent"},
    {"text": "i just want to break something", "intent": "anger_vent"},
    {"text": "my blood is boiling right now", "intent": "anger_vent"},
    {"text": "i cant believe how rude people are", "intent": "anger_vent"},
    {"text": "rage is all i feel right now", "intent": "anger_vent"},

    # ─────────────────────────────────────────────
    # 15. self_doubt (16 messages)
    # ─────────────────────────────────────────────
    {"text": "im not good enough", "intent": "self_doubt"},
    {"text": "i always fail at everything", "intent": "self_doubt"},
    {"text": "why do i keep messing things up", "intent": "self_doubt"},
    {"text": "i feel like a failure", "intent": "self_doubt"},
    {"text": "everyone is better than me", "intent": "self_doubt"},
    {"text": "i dont think ill ever succeed", "intent": "self_doubt"},
    {"text": "whats the point of even trying", "intent": "self_doubt"},
    {"text": "i feel worthless", "intent": "self_doubt"},
    {"text": "i cant do anything right", "intent": "self_doubt"},
    {"text": "nobody believes in me", "intent": "self_doubt"},
    {"text": "i keep letting people down", "intent": "self_doubt"},
    {"text": "im just not talented enough", "intent": "self_doubt"},
    {"text": "i feel like an imposter all the time", "intent": "self_doubt"},
    {"text": "why should anyone care about what i do", "intent": "self_doubt"},
    {"text": "i always second guess myself", "intent": "self_doubt"},
    {"text": "im afraid ill never be good at anything", "intent": "self_doubt"},
]
