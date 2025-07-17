from script.deploy_dsc import deploy_dsc
from script.deploy_dsc_engine import deploy_dsc_engine


def moccasin_main():
    dsc = deploy_dsc()
    deploy_dsc_engine(dsc)
