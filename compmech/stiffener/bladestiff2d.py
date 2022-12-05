import gc

from compmech.panel import Panel
from compmech.logger import msg
from compmech.composite import laminate
from compmech.panel.connections import calc_kt_kr
from .modelDB import db
from compmech.sparse import finalize_symmetric_matrix

class BladeStiff2D(object):
    r"""Blade Stiffener using 2D Formulation for Flange

    Blade-type of stiffener model using a 2D formulation for the flange and a
    2D formulation for the base (padup)::


                 || --> flange       |
                 ||                  |-> stiffener
               ======  --> padup     |
      =========================  --> panels
         Panel1      Panel2

    Both the flange and the base are optional. The stiffener's base is modeled
    using the same approximation functions as the skin, with the proper
    offset.

    Each stiffener has a constant `y_s` coordinate.

    """
    def __init__(self, bay, mu, panel1, panel2, ys, bb, bf, bstack, bplyts,
            blaminaprops, fstack, fplyts, flaminaprops, mf=14, nf=11):
        self.bay = bay
        self.panel1 = panel1
        self.panel2 = panel2
        self.mu = mu
        self.ys = ys
        self.bb = bb
        self.forces_flange = []

        self.bstack = bstack
        self.bplyts = bplyts
        self.blaminaprops = blaminaprops

        self.k0 = None
        self.kM = None
        self.kG0 = None

        self.base = None
        if bstack is not None:
            y1 = self.ys - bb/2.
            y2 = self.ys + bb/2.
            h = 0.5*sum(self.panel1.plyts) + 0.5*sum(self.panel2.plyts)
            hb = sum(self.bplyts)
            self.base = Panel(a=bay.a, b=bay.b, r=bay.r, alphadeg=bay.alphadeg,
                    stack=bstack, plyts=bplyts, laminaprops=blaminaprops,
                    mu=mu, m=bay.m, n=bay.n, offset=(-h/2.-hb/2.),
                    u1tx=bay.u1tx, u1rx=bay.u1rx, u2tx=bay.u2tx, u2rx=bay.u2rx,
                    v1tx=bay.v1tx, v1rx=bay.v1rx, v2tx=bay.v2tx, v2rx=bay.v2rx,
                    w1tx=bay.w1tx, w1rx=bay.w1rx, w2tx=bay.w2tx, w2rx=bay.w2rx,
                    u1ty=bay.u1ty, u1ry=bay.u1ry, u2ty=bay.u2ty, u2ry=bay.u2ry,
                    v1ty=bay.v1ty, v1ry=bay.v1ry, v2ty=bay.v2ty, v2ry=bay.v2ry,
                    w1ty=bay.w1ty, w1ry=bay.w1ry, w2ty=bay.w2ty, w2ry=bay.w2ry,
                    y1=y1, y2=y2)

        self.flange = None
        if fstack is not None:
            self.flange = Panel(m=mf, n=nf, a=bay.a, b=bf, mu=mu,
                    stack=fstack, plyts=fplyts, laminaprops=flaminaprops,
                    model='plate_clt_donnell_bardell',
                    u1tx=0., u1rx=0., u2tx=0., u2rx=0.,
                    v1tx=0., v1rx=0., v2tx=0., v2rx=0.,
                    w1tx=0., w1rx=1., w2tx=0., w2rx=1.,
                    u1ty=1., u1ry=0., u2ty=1., u2ry=0.,
                    v1ty=1., v1ry=0., v2ty=1., v2ry=0.,
                    w1ty=1., w1ry=1., w2ty=1., w2ry=1.)

        self._rebuild()


    def _rebuild(self):
        assert self.panel1.model == self.panel2.model
        assert self.panel1.m == self.panel2.m
        assert self.panel1.n == self.panel2.n
        assert self.panel1.r == self.panel2.r
        assert self.panel1.alphadeg == self.panel2.alphadeg
        if self.flange is not None:
            self.flange.lam = laminate.read_stack(self.flange.stack, plyts=self.flange.plyts,
                                            laminaprops=self.flange.laminaprops)
            self.flange.lam.calc_equivalent_modulus()

        if self.base is not None:
            h = 0.5*sum(self.panel1.plyts) + 0.5*sum(self.panel2.plyts)
            hb = sum(self.bplyts)
            self.dpb = h/2. + hb/2.
            self.base.lam = laminate.read_stack(self.bstack, plyts=self.bplyts,
                                            laminaprops=self.blaminaprops,
                                            offset=(-h/2.-hb/2.))


    def calc_k0(self, size=None, row0=0, col0=0, silent=False, finalize=True):
        """Calculate the linear constitutive stiffness matrix
        """
        self._rebuild()
        msg('Calculating k0... ', level=2, silent=silent)

        bay = self.bay
        a = bay.a
        b = bay.b
        m = bay.m
        n = bay.n

        k0 = 0.
        if self.base is not None:
            k0 += self.base.calc_k0(size=size, row0=0, col0=0, silent=True,
                    finalize=False)
        if self.flange is not None:
            k0 += self.flange.calc_k0(size=size, row0=row0, col0=col0,
                    silent=True, finalize=False)

            # connectivity between stiffener'base and stiffener's flange
            if self.base is None:
                ktbf, krbf = calc_kt_kr(self.panel1, self.flange, 'ycte')
            else:
                ktbf, krbf = calc_kt_kr(self.base, self.flange, 'ycte')

            mod = db['bladestiff2d_clt_donnell_bardell']['connections']
            k0 += mod.fkCss(ktbf, krbf, self.ys, a, b, m, n,
                            bay.u1tx, bay.u1rx, bay.u2tx, bay.u2rx,
                            bay.v1tx, bay.v1rx, bay.v2tx, bay.v2rx,
                            bay.w1tx, bay.w1rx, bay.w2tx, bay.w2rx,
                            bay.u1ty, bay.u1ry, bay.u2ty, bay.u2ry,
                            bay.v1ty, bay.v1ry, bay.v2ty, bay.v2ry,
                            bay.w1ty, bay.w1ry, bay.w2ty, bay.w2ry,
                            size, 0, 0)
            bf = self.flange.b
            k0 += mod.fkCsf(ktbf, krbf, self.ys, a, b, bf, m, n, self.flange.m, self.flange.n,
                            bay.u1tx, bay.u1rx, bay.u2tx, bay.u2rx,
                            bay.v1tx, bay.v1rx, bay.v2tx, bay.v2rx,
                            bay.w1tx, bay.w1rx, bay.w2tx, bay.w2rx,
                            bay.u1ty, bay.u1ry, bay.u2ty, bay.u2ry,
                            bay.v1ty, bay.v1ry, bay.v2ty, bay.v2ry,
                            bay.w1ty, bay.w1ry, bay.w2ty, bay.w2ry,
                            self.flange.u1tx, self.flange.u1rx, self.flange.u2tx, self.flange.u2rx,
                            self.flange.v1tx, self.flange.v1rx, self.flange.v2tx, self.flange.v2rx,
                            self.flange.w1tx, self.flange.w1rx, self.flange.w2tx, self.flange.w2rx,
                            self.flange.u1ty, self.flange.u1ry, self.flange.u2ty, self.flange.u2ry,
                            self.flange.v1ty, self.flange.v1ry, self.flange.v2ty, self.flange.v2ry,
                            self.flange.w1ty, self.flange.w1ry, self.flange.w2ty, self.flange.w2ry,
                            size, 0, col0)
            k0 += mod.fkCff(ktbf, krbf, a, bf, self.flange.m, self.flange.n,
                            self.flange.u1tx, self.flange.u1rx, self.flange.u2tx, self.flange.u2rx,
                            self.flange.v1tx, self.flange.v1rx, self.flange.v2tx, self.flange.v2rx,
                            self.flange.w1tx, self.flange.w1rx, self.flange.w2tx, self.flange.w2rx,
                            self.flange.u1ty, self.flange.u1ry, self.flange.u2ty, self.flange.u2ry,
                            self.flange.v1ty, self.flange.v1ry, self.flange.v2ty, self.flange.v2ry,
                            self.flange.w1ty, self.flange.w1ry, self.flange.w2ty, self.flange.w2ry,
                            size, row0, col0)

        if finalize:
            k0 = finalize_symmetric_matrix(k0)
        self.k0 = k0

        #NOTE forcing Python garbage collector to clean the memory
        #     it DOES make a difference! There is a memory leak not
        #     identified, probably in the csr_matrix process
        gc.collect()

        msg('finished!', level=2, silent=silent)


    def calc_kG0(self, size=None, row0=0, col0=0, silent=False, finalize=True,
            c=None, NLgeom=False):
        """Calculate the linear geometric stiffness matrix
        """
        self._rebuild()
        msg('Calculating kG0... ', level=2, silent=silent)

        kG0 = 0.
        if self.base is not None:
            #TODO include kG0 for pad-up and Nxx load that arrives there
            pass
        if self.flange is not None:
            kG0 += self.flange.calc_kG0(size=size, row0=row0, col0=col0,
                    silent=True, finalize=False, NLgeom=NLgeom)

        if finalize:
            kG0 = finalize_symmetric_matrix(kG0)
        self.kG0 = kG0

        #NOTE forcing Python garbage collector to clean the memory
        #     it DOES make a difference! There is a memory leak not
        #     identified, probably in the csr_matrix process
        gc.collect()

        msg('finished!', level=2, silent=silent)


    def calc_kM(self, size=None, row0=0, col0=0, silent=False, finalize=True):
        """Calculate the mass matrix
        """
        self._rebuild()
        msg('Calculating kM... ', level=2, silent=silent)

        kM = 0.
        if self.base is not None:
            kM += self.base.calc_kM(size=size, row0=0, col0=0, silent=True, finalize=False)
        if self.flange is not None:
            kM += self.flange.calc_kM(size=size, row0=row0, col0=col0, silent=True, finalize=False)

        if finalize:
            kM = finalize_symmetric_matrix(kM)
        self.kM = kM

        #NOTE forcing Python garbage collector to clean the memory
        #     it DOES make a difference! There is a memory leak not
        #     identified, probably in the csr_matrix process
        gc.collect()

        msg('finished!', level=2, silent=silent)

