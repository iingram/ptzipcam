if ! command -v python3.7 &> /dev/null
then
    echo "Python 3.7 not found. Make sure you have 3.7 or higher."
    echo "Aborting dependency install."
    return 1
else
    echo "Python 3.7 was found."
    echo "_____________________"
fi

sudo apt -y install libopencv-dev 
sudo apt -y install libatlas-base-dev
sudo apt -y install libjasper-dev
sudo apt -y install libqt4-dev
