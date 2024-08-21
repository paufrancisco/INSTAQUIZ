from flask import Flask, render_template, request, make_response
from flask_bootstrap import Bootstrap
import spacy
from collections import Counter
import random
from PyPDF2 import PdfReader

app = Flask(__name__)
Bootstrap(app)

# Load English tokenizer, tagger, parser, NER, and word vectors
nlp = spacy.load("en_core_web_lg")

def generate_mcqs(text, num_questions=5):
    if not text:
        return []

    # Process the text with spaCy
    doc = nlp(text)

    # Extract sentences from the text
    sentences = [sent.text for sent in doc.sents]

    # Ensure that the number of questions does not exceed the number of sentences
    num_questions = min(num_questions, len(sentences))

    # Randomly select sentences to form questions
    selected_sentences = random.sample(sentences, num_questions)


    mcqs = []

    for sentence in selected_sentences:
        # Process the sentence with spaCy
        sent_doc = nlp(sentence)

        # Extract nouns from the sentence
        nouns = [token.text for token in sent_doc if token.pos_ == "NOUN"]
        # nouns = [token.text for token in sent_doc if token.pos_ == "NOUN" and token.ent_type_]

        # Ensure there are enough nouns to generate MCQs
        if len(nouns) < 0:
            continue

        # Select the most common noun as the subject of the question
        subject = nouns[0]  # You can modify this to select a more appropriate noun if needed

        # Generate the question stem
        question_stem = sentence.replace(subject, "______")

        # Generate answer choices
        answer_choices = [subject]

        # Add some of the other nouns as distractors
        distractors = list(set(nouns) - {subject})

        # Ensure there are at least three distractors
        while len(distractors) < 3:
            distractors.append("[Distractor]")  # Placeholder for missing distractors

        answer_choices.extend(distractors[:3])
        random.shuffle(answer_choices)

        correct_answer = chr(65 + answer_choices.index(subject))  # Convert index to letter
        mcqs.append((question_stem, answer_choices, correct_answer))

    return mcqs

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = ""

        if 'files[]' in request.files:
            files = request.files.getlist('files[]')
            for file in files:
                if file.filename.endswith('.pdf'):
                    text += process_pdf(file)
                elif file.filename.endswith('.txt'):
                    text += file.read().decode('utf-8')
        else:
            text = request.form.get('text', '')

        num_questions = int(request.form.get('num_questions', 5))

        try:
            mcqs = generate_mcqs(text, num_questions=num_questions)
            mcqs_with_index = [(i + 1, mcq) for i, mcq in enumerate(mcqs)]
            return render_template('mcqs.html', mcqs=mcqs_with_index)
        except Exception as e:
            return f"An error occurred: {e}"

    return render_template('index.html')

def process_pdf(file):
    text = ""
    pdf_reader = PdfReader(file)

    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text

    return text

if __name__ == '__main__':
    app.run(debug=True)
