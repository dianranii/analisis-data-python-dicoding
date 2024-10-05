# analisis-data-python-dicoding

## Setup environment -- Anaconda
conda create --name main-ds python=3.11
conda activate main-ds

## Setup environment -- shell
cd dicoding
cd submission2
python -m venv .venv
.venv\Scripts\activate 
pip install -r requirements.txt

## Run Streamlit
cd dicoding
cd submission2
cd dashboard
streamlit run dicoding_app.py


