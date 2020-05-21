import testing as tm
import pytest
import numpy as np
import json
from pathlib import Path

import securexgboost as xgb
import os
from sklearn.datasets import dump_svmlight_file


username = "user1"
HOME_DIR = os.path.dirname(os.path.realpath(__file__)) + "/../../"
sym_key_file = HOME_DIR + "demo/data/key_zeros.txt"
pub_key_file = HOME_DIR + "demo/data/userkeys/private_user_1.pem"
cert_file = HOME_DIR + "demo/data/usercrts/{0}.crt".format(username)

temp_name = HOME_DIR + "demo/data/temp_file.txt"
temp_enc_name = HOME_DIR + "demo/data/temp_file.txt.enc"

print("Init user parameters")
xgb.init_user(username, sym_key_file, pub_key_file, cert_file)

print("Creating enclave")
enclave = xgb.Enclave(HOME_DIR + "build/enclave/xgboost_enclave.signed")

# Remote Attestation
print("Remote attestation")

# Note: Simulation mode does not support attestation
# pass in `verify=False` to attest()
enclave.attest(verify=False)

print("Send private key to enclave")
enclave.add_key()

dpath = HOME_DIR + 'demo/data/'


def test_aft_survival_toy_data():
    # See demo/aft_survival/aft_survival_viz_demo.py
    X = np.array([1, 2, 3, 4, 5]).reshape((-1, 1))
    INF = np.inf
    y_lower = np.array([ 10,  15, -INF, 30, 100])
    y_upper = np.array([INF, INF,   20, 50, INF])

    #TODO(rishabh): add support for set_float_info()
    """
    dmat = xgb.DMatrix(X)
    dmat.set_float_info('label_lower_bound', y_lower)
    dmat.set_float_info('label_upper_bound', y_upper)

    # "Accuracy" = the number of data points whose ranged label (y_lower, y_upper) includes
    #              the corresponding predicted label (y_pred)
    acc_rec = []
    def my_callback(env):
        y_pred = env.model.predict(dmat)
        acc = np.sum(np.logical_and(y_pred >= y_lower, y_pred <= y_upper)/len(X))
        acc_rec.append(acc)

    evals_result = {}
    params = {'max_depth': 3, 'objective':'survival:aft', 'min_child_weight': 0}
    bst = xgb.train(params, dmat, 15, [(dmat, 'train')], evals_result=evals_result,
                    callbacks=[my_callback])

    nloglik_rec = evals_result['train']['aft-nloglik']
    # AFT metric (negative log likelihood) improve monotonically
    assert all(p >= q for p, q in zip(nloglik_rec, nloglik_rec[:1]))
    # "Accuracy" improve monotonically.
    # Over time, XGBoost model makes predictions that fall within given label ranges.
    assert all(p <= q for p, q in zip(acc_rec, acc_rec[1:]))
    assert acc_rec[-1] == 1.0

    def gather_split_thresholds(tree):
        if 'split_condition' in tree:
            return (gather_split_thresholds(tree['children'][0])
                    | gather_split_thresholds(tree['children'][1])
                    | {tree['split_condition']})
        return set()

    # Only 2.5, 3.5, and 4.5 are used as split thresholds.
    model_json = [json.loads(e) for e in bst.get_dump(dump_format='json')]
    for tree in model_json:
        assert gather_split_thresholds(tree).issubset({2.5, 3.5, 4.5})
    """

@pytest.mark.skipif(**tm.no_pandas())  
def test_aft_survival_demo_data():
    import pandas as pd
    df = pd.read_csv(dpath + 'veterans_lung_cancer.csv')

    y_lower_bound = df['Survival_label_lower_bound']
    y_upper_bound = df['Survival_label_upper_bound']
    X = df.drop(['Survival_label_lower_bound', 'Survival_label_upper_bound'], axis=1)

    #TODO(rishabh): add support for set_float_info()
    """
    dtrain = xgb.DMatrix(X)
    dtrain.set_float_info('label_lower_bound', y_lower_bound)
    dtrain.set_float_info('label_upper_bound', y_upper_bound)

    base_params = {'verbosity': 0,
                   'objective': 'survival:aft',
                   'eval_metric': 'aft-nloglik',
                   'tree_method': 'hist',
                   'learning_rate': 0.05,
                   'aft_loss_distribution_scale': 1.20,
                   'max_depth': 6,
                   'lambda': 0.01,
                   'alpha': 0.02}
    nloglik_rec = {}
    dists = ['normal', 'logistic', 'extreme']
    for dist in dists:
        params = base_params
        params.update({'aft_loss_distribution': dist})
        evals_result = {}
        bst = xgb.train(params, dtrain, num_boost_round=500, evals=[(dtrain, 'train')],
                        evals_result=evals_result)
        nloglik_rec[dist] = evals_result['train']['aft-nloglik']
        # AFT metric (negative log likelihood) improve monotonically
        assert all(p >= q for p, q in zip(nloglik_rec[dist], nloglik_rec[dist][:1]))
    # For this data, normal distribution works the best
    assert nloglik_rec['normal'][-1] < 4.9
    assert nloglik_rec['logistic'][-1] > 4.9
    assert nloglik_rec['extreme'][-1] > 4.9
    """
