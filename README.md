# VERIFYNOW

## PROJECT OVERVIEW

VerifyNow is a web based fake news detection and verification system. The project is designed as a Final Year Project and focuses on helping users verify the credibility of news content and URLs using machine learning assisted analysis and supporting metadata.

The system targets misinformation at the point of consumption by allowing users to submit text or links and receive a credibility assessment supported by historical verification records and source reliability data.

## CORE OBJECTIVES

1. Detect potentially fake or misleading news content
2. Provide credibility scores and classification results
3. Track historical verification results for transparency
4. Maintain source reliability and top reported domains
5. Deliver a clean and user friendly verification workflow

## KEY FEATURES

1. News Text Verification

   * Users can submit news content directly
   * System classifies content as valid or invalid

2. URL Verification

   * Users can submit news article URLs
   * Domain and content are analyzed

3. Verification History

   * Past verification records displayed in a table
   * Includes result status, date, and details popup

4. Source Reliability Management

   * Admin controlled source reliability ratings
   * Used to enhance verification confidence

5. Top Reported Domains

   * Tracks frequently reported domains
   * Supports transparency and analysis

6. Statistics and Analytics

   * Summary level insights for verification trends

## SYSTEM ARCHITECTURE

Frontend

* HTML
* CSS
* JavaScript

Backend

* Python
* Flask

Database

* phpMyAdmin

Machine Learning

* Random Forest Classifier

## PROJECT STRUCTURE

flask_app/

* routes
* services
* templates
* static
* models

ML/

* trained model
* preprocessing logic

## DATABASE TABLES

* users
* verifications
* source_reliability
* top_reported_domains

## INSTALLATION AND SETUP

1. Clone the repository
2. Create a Python virtual environment
3. Install required dependencies
4. Configure database connection
5. Run Flask application

## Example commands

python -m venv venv
pip install -r requirements.txt
flask run

## USAGE FLOW

1. User opens verification page
2. User submits text or URL
3. System processes input
4. ML model returns prediction
5. Result is stored and displayed

## LIMITATIONS

* Model accuracy depends on training data quality
* Real time fact checking against live news sources is limited
* System is intended for educational and research purposes

## FUTURE ENHANCEMENTS

* Improve model accuracy with larger datasets
* Add multilingual support
* Integrate real time fact checking APIs
* Role based access control for admin features

## PROJECT STATUS

Final Year Project
Completed and archived

## AUTHOR

Developed by MTNC
