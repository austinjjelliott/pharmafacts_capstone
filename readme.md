## PharmaFacts

### Overview

PharmaFacts is an easy and accurate way to look up FDA-approved medication facts for both over the counter and prescription pharmaceuticals. Simply search for a drug to learn about its brand/generic names, ingredients, purpose, warnings, indications, dosage, adverse reactions, and storage requirements. Sign up to bookmark medications for easy access, or browse the site easily as a non-verified user.

### Tech Stack

#### Front End

- HTML
- CSS
- Bootstrap

#### Back End

- Python/Flask
- SQLAlchemy
- PostgreSQL
- Jinja
- WTForms
- Bcrypt

### Goal

The main goal of this project is to create a free and informative website where users can access medication information

### Target Users

This information could be interesting to a wide variety of people - pharmacists and medical professionals, students in such fields, or patients who have been prescribed or recommended new medications

### API

This site uses the free openFDA API available at:
`https://open.fda.gov/apis/`

### Live Demo

Check out the live demo on Render:

### Project Breakdown

#### Database Models

- User:
  - username
  - password
  - email
  - first_name
  - last_name
  - bookmarks(db.relationship('Bookmark')...
- Bookmark:
  - brand_name
  - generic_name
  - active_ingredient
  - purpose
  - warnings
  - indications
  - dosage
  - adverse_reactions
  - storage

#### Additional Functionality

- User Authentication/Authorization: Signup and login functionality, protected with bcrypt.
- Search for medications whether signed in or not
- Save results for fast access when signed in
