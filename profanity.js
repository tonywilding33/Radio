// profanity.js
const profanityList = [
    "anal", "anus", "arse", "ass", "asshole", "bastard", "bitch", "bloody", "bollock", "bollocks",
    "boner", "boob", "bugger", "butt", "butthole", "crap", "cunt", "damn", "dick", "dildo",
    "dyke", "fag", "faggot", "feck", "felch", "fuck", "fucked", "fucker", "fucking", "gook",
    "hell", "homo", "jerk", "jizz", "kike", "knob", "labia", "lmao", "lmfao", "mothafucka",
    "mmotherfucker", "mound", "muff", "nigga", "nigger", "orgasm", "penis", "piss", "poop", "prick",
    "pube", "pussy", "queef", "queer", "rimjob", "scrotum", "sex", "shit", "shited", "shite",
    "shitting", "shitty", "slut", "smegma", "spunk", "tit", "tits", "titties", "tosser", "turd",
    "twat", "vagina", "wank", "wanker", "whore", "wtf", "asshat", "asswipe", "clusterfuck", "cock",
    "cocksucker", "cum", "cumshot", "cunnilingus", "deepthroat", "doggystyle", "douche", "douchebag", "eatass", "fellate",
    "fellatio", "handjob", "masterbate", "masturbate", "milf", "muffdiver", "pedo", "pedophile", "potty", "renob"
];

function filterProfanity(text) {
    if (!text) return '';
    let filteredText = text;
    profanityList.forEach(word => {
        const regex = new RegExp('\\b' + word + '\\b', 'gi');
        filteredText = filteredText.replace(regex, '*'.repeat(word.length));
    });
    return filteredText;
}