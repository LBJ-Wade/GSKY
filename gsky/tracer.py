import pymaster as nmt
import numpy as np
from .flatmaps import compare_infos, read_flat_map

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Tracer(object) :
    def __init__(self, hdu_list, i_bin, fsk, mask_binary, masked_fraction, contaminants=None, type='ngal_maps',
                 weightmask=True, beam=None):
        """
        Class used to define the information stored in each of the number density maps generated by CatMapper, which are then transformed into overdensity maps.
        :param hdu_list: list of FITS HDUs containing the number density maps.
        :param i_bin: which redshift bin to consider.
        :param fsk: flatmaps.FlatSkyInfo object defining the geometry of the maps.
        :param mask_binary: binary mask (which pixels to consider and which not to).
        :param masked_fraction: masked fraction map.
        :param contaminants: list of possible contaminant maps to deproject.
        
        This class then stores a number of data objects, the most important one being a pymaster `NmtFieldFlat` ready to use in power spectrum estimation.
        """

        if type == 'ngal_maps':
            logger.info('Creating tracer object for number density.')
            self.type = 'galaxy_density'
            self.spin = 0
            #Read numbers map
            self.fsk,nmap=read_flat_map(None,hdu=hdu_list[2*i_bin])
            compare_infos(fsk,self.fsk)

            #Read N(z)
            self.nz_data=hdu_list[2*i_bin+1].data.copy()

            #Make sure other maps are compatible
            if not self.fsk.is_map_compatible(mask_binary) :
                raise ValueError("Mask size is incompatible")
            if not self.fsk.is_map_compatible(masked_fraction) :
                raise ValueError("Mask size is incompatible")
            if contaminants is not None :
                for ic,c in enumerate(contaminants) :
                    if not self.fsk.is_map_compatible(c) :
                        raise ValueError("%d-th contaminant template is incompatible"%ic)

            #Translate into delta map
            self.masked_fraction=masked_fraction
            self.weight=masked_fraction*mask_binary
            goodpix=np.where(mask_binary>0.1)[0]
            self.goodpix=goodpix
            self.mask_binary=mask_binary
            self.Ngal = np.sum(nmap*mask_binary)
            ndens=np.sum(nmap*mask_binary)/np.sum(self.weight)
            self.ndens_perad=ndens/(np.radians(self.fsk.dx)*np.radians(self.fsk.dy))
            self.delta=np.zeros_like(self.weight)
            self.delta[goodpix]=nmap[goodpix]/(ndens*masked_fraction[goodpix])-1

            #Reshape contaminants
            conts=None
            if contaminants is not None :
                conts=[[c.reshape([self.fsk.ny,self.fsk.nx])] for c in contaminants]

            #Form NaMaster field
            self.field=nmt.NmtFieldFlat(np.radians(self.fsk.lx),np.radians(self.fsk.ly),
                                        self.weight.reshape([self.fsk.ny,self.fsk.nx]),
                                        [self.delta.reshape([self.fsk.ny,self.fsk.nx])],
                                        templates=conts)

        elif type == 'shear_maps':
            logger.info('Creating tracer object for shear.')
            self.type = 'galaxy_shear'
            self.spin = 2
            # Read shear map
            self.fsk, gammamaps = read_flat_map(None, hdu=[hdu_list[6*i_bin], hdu_list[6*i_bin+1]])
            compare_infos(fsk, self.fsk)

            _, masks = read_flat_map(None, hdu=[hdu_list[6*i_bin+2], hdu_list[6*i_bin+3], hdu_list[6*i_bin+4]])

            #Read N(z)
            self.nz_data=hdu_list[6*i_bin+5].data.copy()

            # Make sure other maps are compatible
            if not self.fsk.is_map_compatible(masks[0]) :
                raise ValueError("Weightmask size is incompatible.")
            if not self.fsk.is_map_compatible(masks[1]) :
                raise ValueError("Binary mask size is incompatible.")
            if contaminants is not None :
                for ic,c in enumerate(contaminants) :
                    if not self.fsk.is_map_compatible(c) :
                        raise ValueError("%d-th contaminant template is incompatible."%ic)

            self.weight = masks[0]
            mask_binary = masks[1]
            nmap = masks[2]

            # Reshape contaminants
            conts = None
            if contaminants is not None:
                conts = [[c.reshape([self.fsk.ny, self.fsk.nx])] for c in contaminants]

            ndens = np.sum(nmap * mask_binary) / np.sum(self.weight)
            self.ndens_perad = ndens / (np.radians(self.fsk.dx) * np.radians(self.fsk.dy))
            self.e1_2rms_pix = np.average(gammamaps[0]**2, weights=self.weight)
            self.e2_2rms_pix = np.average(gammamaps[1] ** 2, weights=self.weight)
            e1_2rms_cat, e2_2rms_cat = hdu_list[-1].data['e2rms'][i_bin, :].copy()
            self.e1_2rms_cat = e1_2rms_cat
            self.e2_2rms_cat = e2_2rms_cat
            if 'w2e2' in hdu_list[-1].columns.names:
                logger.info('Found w2e2 attribute.')
                self.w2e2 = hdu_list[-1].data['w2e2'][i_bin].copy()

            # Form NaMaster field
            if weightmask:
                logger.info('Using weight mask.')
                self.field = nmt.NmtFieldFlat(np.radians(self.fsk.lx), np.radians(self.fsk.ly),
                            self.weight.reshape([self.fsk.ny,self.fsk.nx]),
                            [gammamaps[0].reshape([self.fsk.ny,self.fsk.nx]), gammamaps[1].reshape([self.fsk.ny,self.fsk.nx])],
                            templates=conts)
            else:
                logger.info('Using binary mask.')
                self.field = nmt.NmtFieldFlat(np.radians(self.fsk.lx), np.radians(self.fsk.ly),
                            mask_binary.reshape([self.fsk.ny,self.fsk.nx]),
                            [gammamaps[0].reshape([self.fsk.ny,self.fsk.nx]), gammamaps[1].reshape([self.fsk.ny,self.fsk.nx])],
                            templates=conts)

        elif type == 'Compton_y_maps':
            logger.info('Creating tracer object for Compton_y.')
            self.type = 'cmb_tSZ'
            self.spin = 0
            # Read tSZ map
            self.fsk, tszmap = read_flat_map(None, hdu=hdu_list[i_bin])
            compare_infos(fsk, self.fsk)

            _, mask = read_flat_map(None, hdu=hdu_list[i_bin+1])

            # Make sure other maps are compatible
            if not self.fsk.is_map_compatible(mask) :
                raise ValueError("Mask size is incompatible.")
            if contaminants is not None :
                for ic,c in enumerate(contaminants) :
                    if not self.fsk.is_map_compatible(c) :
                        raise ValueError("%d-th contaminant template is incompatible."%ic)

            # Reshape contaminants
            conts = None
            if contaminants is not None:
                conts = [[c.reshape([self.fsk.ny, self.fsk.nx])] for c in contaminants]

            self.beam = beam

            # Form NaMaster field
            self.field=nmt.NmtFieldFlat(np.radians(self.fsk.lx),np.radians(self.fsk.ly),
                                        mask.reshape([self.fsk.ny,self.fsk.nx]),
                                        [tszmap.reshape([self.fsk.ny,self.fsk.nx])],
                                        templates=conts, beam=beam)

        elif type == 'kappa_maps':
            logger.info('Creating tracer object for kappa.')
            self.type = 'cmb_convergence'
            self.spin = 0
            # Read kappa map
            self.fsk, kappamap = read_flat_map(None, hdu=hdu_list[i_bin])
            compare_infos(fsk, self.fsk)

            _, mask = read_flat_map(None, hdu=hdu_list[i_bin+1])

            # Make sure other maps are compatible
            if not self.fsk.is_map_compatible(mask) :
                raise ValueError("Mask size is incompatible.")
            if contaminants is not None :
                for ic,c in enumerate(contaminants) :
                    if not self.fsk.is_map_compatible(c) :
                        raise ValueError("%d-th contaminant template is incompatible."%ic)

            # Reshape contaminants
            conts = None
            if contaminants is not None:
                conts = [[c.reshape([self.fsk.ny, self.fsk.nx])] for c in contaminants]

            # Form NaMaster field
            self.field=nmt.NmtFieldFlat(np.radians(self.fsk.lx),np.radians(self.fsk.ly),
                                        mask.reshape([self.fsk.ny,self.fsk.nx]),
                                        [kappamap.reshape([self.fsk.ny,self.fsk.nx])],
                                        templates=conts)

        else:
            raise NotImplementedError('Only map types = ngal_maps, gamma_maps, Compton_y maps, kappa_maps currently supported.')