if [[ $(uname -a) == *"cent7"* ]]; then
    # centos7
    setupATLAS -q
    export PIP_NO_CACHE_DIR=off
    lsetup "views LCG_98python3 x86_64-centos7-gcc9-opt"
    export PYTHONPATH=/cvmfs/sft.cern.ch/lcg/views/LCG_98python3/x86_64-centos7-gcc9-opt/python:/cvmfs/sft.cern.ch/lcg/views/LCG_98python3/x86_64-centos7-gcc9-opt/lib
elif [[ $(uname -a) == *"slc6"* ]]; then
    # slc6
    setupATLAS -q
    export PIP_NO_CACHE_DIR=off
    lsetup "views LCG_98bpython3 x86_64-centos7-gcc8-opt"
    export PYTHONPATH=/cvmfs/sft.cern.ch/lcg/views/LCG_98bpython3/x86_64-slc6-gcc8-opt/python:/cvmfs/sft.cern.ch/lcg/views/LCG_98bpython3/x86_64-slc6-gcc8-opt/lib
fi

if [ -f "py_CARLTorch/bin/activate" ]; then
    source py_CARLTorch/bin/activate
else
    python -m venv py_CARLTorch
    source py_CARLTorch/bin/activate
    python -m pip install -U pip setuptools wheel
    echo 'Now run `python -m pip install -e .'
fi
