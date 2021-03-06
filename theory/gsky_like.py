import numpy as np

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GSKYLike(object):

    def __init__ (self, saccfile, noise_saccfile=None):

        self.setup_data(saccfile, noise_saccfile)

    def computeLike(self, obs_theory):

        # Calculate a likelihood up to normalization
        delta = self.obs_data - obs_theory
        lnprob = np.einsum('i,ij,j', delta, self.invcov, delta)
        lnprob *= -0.5

        # Return the likelihood
        return lnprob

    def setup_data(self, saccfile, noise_saccfile):

        self.obs_data = saccfile.mean
        if noise_saccfile is not None:
            self.obs_data -= noise_saccfile.mean
        self.invcov = np.linalg.inv(saccfile.covariance.covmat)




