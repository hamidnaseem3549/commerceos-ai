#!/bin/sh
set -e

echo "CommerceOS AI — Starting up..."
python -c "from commerceos.database.connection import init_db; init_db()"
python scripts/seed.py

if [ ! -f "ui/assets/images/product_p1001.svg" ]; then
    python ui/assets/images/gen_placeholders.py
fi

exec streamlit run app.py --server.port=8501 --server.address=0.0.0.0
