ruscorpora_tagging
==================

Text tokenization and annotation scripts for Ruscorpora
--

- `tokenizer.py`: annotates text with sentence `<se>` and word `<w>` tags.
Uses punctuation and `<p>`, `<tr>`, `<td>`, `<th>`, `<table>`, `<body>` tags as sentence delimiters.

- `morpho_tagger.py`: adds grammatical analysis `<ana>`; tags to the words.
Splits compound words into extra `<w>`-parts according to the output of the lemmatizer.

- `annotate_texts.py`: the complete two-stage tagging. Used with regular morpho_tagger options.

Requiremenets
--

- Python dependencies (run `pip install -r requirements.txt`);
- a copy of `mystem_ruscorpora` binary (please contact info@ruscorpora.ru for inquiries).

