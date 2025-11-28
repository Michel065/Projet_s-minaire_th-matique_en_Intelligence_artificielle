@echo off
echo Activation de l'environnement virtuel tf-cuda-win...

call C:\Users\Maste\anaconda3\Scripts\activate.bat tf-cuda-win

echo Lancement du serveur Flask...
python server_web.py

pause
