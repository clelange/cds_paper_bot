"""Test title formatting."""
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import cds_paper_bot  # pylint: disable=wrong-import-position,import-error


class TestFormatTitle(object):
    """List of titles and what they should look like after formatting."""

    @pytest.mark.parametrize(
        "input_title, expected",
        [
            ("Analysis at $\\sqrt s=13 TeV$", "Analysis at √(s) = 13 TeV"),
            ("\\sqrt s", "√(s)"),
            ("Analysis  of process $x \\rightarrowy$", "Analysis of process x → y"),
            ("$x__s$", "x_s"),
            ("x →y", "x → y"),
            ("$t\\overline tt$", "ttt"),
            ("$t\\bar{t}$", "tt̅"),
            ("$t \\bar{t}$", "tt̅"),
            ("$t \\overline t$", "tt"),
            ("\\overline xy", "xy"),
            ("Bethe--Bloch", "Bethe–Bloch"),
            ("Bethe---Bloch", "Bethe—Bloch"),
            ("Energies of 15keV and MeV, 6eV", "Energies of 15 keV and MeV, 6 eV"),
            ("13TeV", "13 TeV"),
            ("nonsenseTeV", "nonsenseTeV"),
            ("13tev", "13tev"),
            ("50eV", "50 eV"),
            # pylint: disable=line-too-long,too-many-lines
            # CMS cms_pas_feed
            (
                "Measurement of differential ${\\mathrm t}\\bar{\\mathrm t}$ production cross sections for high-$p_{\\text{T}}$ top quarks in proton-proton collisions at $\\sqrt{s} = 13\\,\\text{TeV}$",
                "Measurement of differential tt̅ production cross sections for high-p_T top quarks in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for long-lived particles decaying into displaced jets",
                "Search for long-lived particles decaying into displaced jets",
            ),
            (
                "Study of hard color singlet exchange in dijet events with proton-proton collisions at $\\sqrt{s}= 13~\\mathrm{TeV}$",
                "Study of hard color singlet exchange in dijet events with proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Inclusive search for a highly boosted Higgs boson decaying to a bottom quark-antiquark pair at $\\sqrt{s} = 13~\\mathrm{TeV}$ with $137~\\mathrm{fb}^{-1}$",
                "Inclusive search for a highly boosted Higgs boson decaying to a bottom quark-antiquark pair at √(s) = 13 TeV with 137 fb⁻¹",
            ),
            (
                "Observation of heavy triboson production in leptonic final states in proton-proton collisions at $\\sqrt{s}=13~\\mathrm{TeV}$",
                "Observation of heavy triboson production in leptonic final states in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Studies of $\\mathrm{W^+W^-}$ production at $\\sqrt{s}=13~\\mathrm{TeV}$",
                "Studies of W⁺W⁻ production at √(s) = 13 TeV",
            ),
            (
                "Measurement of the $CP$ violating phase $\\phi_{\\text{s}}$ in the $\\mathrm{B}_s \\to \\mathrm{J}/\\psi\\,\\phi(1020) \\to \\mu^+\\mu^-\\,\\mathrm{K}^+\\mathrm{K}^-$ channel in proton-proton collisions at $\\sqrt{s} = 13~\\mathrm{TeV}$",
                "Measurement of the CP violating phase ϕ_s in the B_s → J/ψ ϕ(1020) → μ⁺μ⁻ K⁺K⁻ channel in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Measurements of production cross sections of same-sign WW and WZ boson pairs in association with two jets in proton-proton collisions at sqrts = 13 TeV",
                "Measurements of production cross sections of same-sign WW and WZ boson pairs in association with two jets in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Measurement of differential cross sections for single top quark production in association with a W boson at $\\sqrt{s}=13~\\mathrm{TeV}$",
                "Measurement of differential cross sections for single top quark production in association with a W boson at √(s) = 13 TeV",
            ),
            (
                "Measurement of the W boson rapidity, helicity, and differential cross sections in pp collisions at $\\sqrt{s}=13~\\mathrm{TeV}$",
                "Measurement of the W boson rapidity, helicity, and differential cross sections in pp collisions at √(s) = 13 TeV",
            ),
            (
                "Search for disappearing tracks in proton-proton collisions at $\\sqrt{s} = 13$ TeV",
                "Search for disappearing tracks in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Combined Higgs boson production and decay measurements with up to 137 fb-1 of proton-proton collision data at sqrts = 13 TeV",
                "Combined Higgs boson production and decay measurements with up to 137 fb-1 of proton-proton collision data at √(s) = 13 TeV",
            ),
            (
                "Search for a light charged Higgs boson in the H$^{\\pm} \\rightarrow$ cs channel at 13 TeV",
                "Search for a light charged Higgs boson in the H^± → cs channel at 13 TeV",
            ),
            (
                "Measurement of prompt $\\rm{ D_{s}^{+}}$ production in pp and PbPb collisions at $\\sqrt{s_{_{\\text{NN}}}}$ = 5.02 TeV",
                "Measurement of prompt D⁺_s production in pp and PbPb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Extraction of CKM matrix elements in single top quark $t$-channel events in proton-proton collisions at $\\sqrt{s} = 13$ TeV",
                "Extraction of CKM matrix elements in single top quark t-channel events in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Nuclear modification factor of isolated photons in PbPb collisions at $\\sqrt{s_{_{\\mathrm{NN}}}} = 5.02~\\mathrm{TeV}$",
                "Nuclear modification factor of isolated photons in PbPb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Nuclear modification of $\\Upsilon$ states in pPb collisions at $\\sqrt{s_\\mathrm{NN}} = 5.02~\\mathrm{TeV}$",
                "Nuclear modification of Υ states in pPb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Search for strong electromagnetic fields in PbPb collisions at 5.02 TeV via azimuthal anisotropy of $\\mathrm{D^0}$ and $\\mathrm{\\overline{D}^0}$ mesons",
                "Search for strong electromagnetic fields in PbPb collisions at 5.02 TeV via azimuthal anisotropy of D⁰ and D̅⁰ mesons",
            ),
            (
                "Studies of charm and beauty long-range correlations in pp and pPb collisions",
                "Studies of charm and beauty long-range correlations in pp and pPb collisions",
            ),
            (
                "Evidence for top quark production in nucleus-nucleus collisions",
                "Evidence for top quark production in nucleus-nucleus collisions",
            ),
            (
                "Evidence for $\\chi_{c1}$(3872) in PbPb collisions and studies of its prompt production at $\\sqrt{\\smash[b]{s_{_{\\mathrm{NN}}}}}=5.02$ TeV",
                "Evidence for χ_c1(3872) in PbPb collisions and studies of its prompt production at √(s_NN) = 5.02 TeV",
            ),
            (
                "Study of quark- and gluon-like jet fractions using jet charge in PbPb and pp collisions at 5.02 TeV",
                "Study of quark- and gluon-like jet fractions using jet charge in PbPb and pp collisions at 5.02 TeV",
            ),
            (
                "Measurement of the elliptic flow of $\\Upsilon\\textrm{(1S)}$ and $\\Upsilon\\textrm{(2S)}$ mesons in PbPb collisions at $\\sqrt{\\mathrm{s_{NN}}}=5.02~\\mathrm{TeV}$",
                "Measurement of the elliptic flow of Υ(1S) and Υ(2S) mesons in PbPb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Measurement of Jet Nuclear Modification Factor in PbPb Collisions at $\\sqrt{s_{NN}}$ = 5.02 TeV with CMS",
                "Measurement of Jet Nuclear Modification Factor in PbPb Collisions at √(s_NN) = 5.02 TeV with CMS",
            ),
            (
                "Measurement of $\\mathrm{b}$ jet shapes in pp collisions at $\\sqrt{s} = 5.02~\\mathrm{TeV}$",
                "Measurement of b jet shapes in pp collisions at √(s) = 5.02 TeV",
            ),
            (
                "Measurement of the average very forward energy as a function of the track multiplicity at central rapidities in proton-proton collisions at $\\sqrt{s}=13~\\mathrm{TeV}$",
                "Measurement of the average very forward energy as a function of the track multiplicity at central rapidities in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for direct $\\tau$ slepton pair production in proton-proton collisions at $\\sqrt{s}=13~\\mathrm{TeV}$",
                "Search for direct τ slepton pair production in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for heavy resonances in the all-hadronic vector-boson pair final state with a multi-dimensional fit",
                "Search for heavy resonances in the all-hadronic vector-boson pair final state with a multi-dimensional fit",
            ),
            (
                "Study of the $\\mathrm{B}^{+}\\rightarrow \\mathrm{J}/\\psi \\bar{\\Lambda} \\mathrm{p}$ decay in proton-proton collisions at $\\sqrt{s}= 8~\\mathrm{TeV}$",
                "Study of the B⁺ → J/ψΛ̅p decay in proton-proton collisions at √(s) = 8 TeV",
            ),
            (
                "Search for new physics in multilepton final states in pp collisions at $\\sqrt{s}=13~\\mathrm{TeV}$",
                "Search for new physics in multilepton final states in pp collisions at √(s) = 13 TeV",
            ),
            (
                "Measurement of the $\\textrm{pp} \\rightarrow \\textrm{Z}\\textrm{Z}$ production cross section at $\\sqrt{s} = 13$ TeV with the Run 2 data set",
                "Measurement of the pp → ZZ production cross section at √(s) = 13 TeV with the Run 2 data set",
            ),
            (
                "Search for standard model production of four top quarks in final states with same-sign and multiple leptons in proton-proton collisions at $\\sqrt{s}=13~\\mathrm{TeV}$",
                "Search for standard model production of four top quarks in final states with same-sign and multiple leptons in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for a heavy Higgs boson decaying to a pair of W bosons in proton-proton collisions at $\\sqrt{s}=13~\\mathrm{TeV}$",
                "Search for a heavy Higgs boson decaying to a pair of W bosons in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for heavy Higgs bosons decaying to a top quark pair in proton-proton collisions at $\\sqrt{s} = 13\\,\\mathrm{TeV}$",
                "Search for heavy Higgs bosons decaying to a top quark pair in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Measurement of Higgs boson production and decay to the $\\tau\\tau$ final state",
                "Measurement of Higgs boson production and decay to the ττ final state",
            ),
            (
                "Measurements of properties of the Higgs boson in the four-lepton final state in proton-proton collisions at $\\sqrt{s}=13~\\mathrm{TeV}$",
                "Measurements of properties of the Higgs boson in the four-lepton final state in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "First constraints on invisible Higgs boson decays using $\\mathrm{t}\\bar{\\mathrm{t}}\\mathrm{H}$ production at $\\sqrt{s}=13~\\mathrm{TeV}$",
                "First constraints on invisible Higgs boson decays using tt̅H production at √(s) = 13 TeV",
            ),
            (
                "Combined search for gauge-mediated supersymmetry with photons in 13 TeV collisions at the CMS experiment",
                "Combined search for gauge-mediated supersymmetry with photons in 13 TeV collisions at the CMS experiment",
            ),
            (
                "Evidence for WW production from double-parton interactions in proton-proton collisions at $\\sqrt{s}$ = 13 TeV",
                "Evidence for WW production from double-parton interactions in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for $\\tau \\to 3\\mu$ decays using $\\tau$ leptons produced in D and B meson decays",
                "Search for τ → 3μ decays using τ leptons produced in D and B meson decays",
            ),
            (
                "Search for physics beyond the standard model in events with two same-sign leptons or at least three leptons and jets in proton-proton collisions at $\\sqrt{s}=13~\\mathrm{TeV}$.",
                "Search for physics beyond the standard model in events with two same-sign leptons or at least three leptons and jets in proton-proton collisions at √(s) = 13 TeV.",
            ),
            (
                "Searches for new phenomena in events with jets and high values of the $M_{\\mathrm{T2}}$ variable, including signatures with disappearing tracks, in proton-proton collisions at $\\sqrt{s}=13~\\mathrm{TeV}$",
                "Searches for new phenomena in events with jets and high values of the M_T2 variable, including signatures with disappearing tracks, in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for long-lived particles using delayed jets and missing transverse momentum with proton-proton collisions at $\\sqrt{s}$ = 13 TeV",
                "Search for long-lived particles using delayed jets and missing transverse momentum with proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for excited leptons decaying via contact interaction to two leptons and two jets",
                "Search for excited leptons decaying via contact interaction to two leptons and two jets",
            ),
            (
                "Search for a pseudoscalar boson in the mass range from 4 to 15 GeV produced in decays of the 125 GeV Higgs boson in the final states with two muons and two nearby tracks at $\\sqrt{s}=13~\\mathrm{TeV}$",
                "Search for a pseudoscalar boson in the mass range from 4 to 15 GeV produced in decays of the 125 GeV Higgs boson in the final states with two muons and two nearby tracks at √(s) = 13 TeV",
            ),
            (
                "Search for boosted quark-antiquark resonances produced in association with a photon at $\\sqrt{s}=13~\\mathrm{TeV}$",
                "Search for boosted quark-antiquark resonances produced in association with a photon at √(s) = 13 TeV",
            ),
            (
                "Search for new physics in events with closely collimated photons and gluons",
                "Search for new physics in events with closely collimated photons and gluons",
            ),
            (
                "Search for Pair Production of Vector-Like Quarks in the Fully Hadronic Channel",
                "Search for Pair Production of Vector-Like Quarks in the Fully Hadronic Channel",
            ),
            (
                "Measurements of Higgs boson production via gluon fusion and vector boson fusion in the diphoton decay channel at $\\sqrt{s} = 13$ TeV",
                "Measurements of Higgs boson production via gluon fusion and vector boson fusion in the diphoton decay channel at √(s) = 13 TeV",
            ),
            (
                "Search for a charged Higgs boson decaying into top and bottom quarks in proton-proton collisions at 13TeV in events with electrons or muons",
                "Search for a charged Higgs boson decaying into top and bottom quarks in proton-proton collisions at 13 TeV in events with electrons or muons",
            ),
            # CMS cms_paper_feed
            (
                "Combination of the W boson polarization measurements in top quark decays using ATLAS and CMS data at $\\sqrt{s} = $ 8 TeV",
                "Combination of the W boson polarization measurements in top quark decays using ATLAS and CMS data at √(s) = 8 TeV",
            ),
            (
                "Measurements of production cross sections of WZ and same-sign WW boson pairs in association with two jets in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Measurements of production cross sections of WZ and same-sign WW boson pairs in association with two jets in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Measurement of CKM matrix elements in single top quark $t$-channel production in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Measurement of CKM matrix elements in single top quark t-channel production in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Identification of heavy, energetic, hadronically decaying particles using machine-learning techniques",
                "Identification of heavy, energetic, hadronically decaying particles using machine-learning techniques",
            ),
            (
                "Search for disappearing tracks in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Search for disappearing tracks in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Measurement of quark- and gluon-like jet fractions using jet charge in PbPb and pp collisions at 5.02 TeV",
                "Measurement of quark- and gluon-like jet fractions using jet charge in PbPb and pp collisions at 5.02 TeV",
            ),
            (
                "The production of isolated photons in PbPb and pp collisions at ${\\sqrt {\\smash [b]{s_{_{\\mathrm {NN}}}}}} = $ 5.02 TeV",
                "The production of isolated photons in PbPb and pp collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Measurements of ${\\mathrm{t\\bar{t}}\\mathrm{H}} $ production and the CP structure of the Yukawa interaction between the Higgs boson and top quark in the diphoton decay channel",
                "Measurements of tt̅H production and the CP structure of the Yukawa interaction between the Higgs boson and top quark in the diphoton decay channel",
            ),
            (
                "Measurement of the cross section for $\\mathrm{t\\bar{t}}$ production with additional jets and b jets in pp collisions at $\\sqrt{s} = $ 13 TeV",
                "Measurement of the cross section for tt̅ production with additional jets and b jets in pp collisions at √(s) = 13 TeV",
            ),
            (
                "Study of central exclusive $\\pi^{+}\\pi^{-}$ production in proton-proton collisions at $\\sqrt{s} = $ 5.02 and 13 TeV",
                "Study of central exclusive π⁺π⁻ production in proton-proton collisions at √(s) = 5.02 and 13 TeV",
            ),
            (
                "Pileup mitigation at CMS in 13 TeV data",
                "Pileup mitigation at CMS in 13 TeV data",
            ),
            (
                "Measurement of single-diffractive dijet production in proton-proton collisions at $\\sqrt{s} =$ 8 TeV with the CMS and TOTEM experiments",
                "Measurement of single-diffractive dijet production in proton-proton collisions at √(s) = 8 TeV with the CMS and TOTEM experiments",
            ),
            (
                "Measurement of the cross section for electroweak production of a Z boson, a photon and two jets in proton-proton collisions at $\\sqrt{s} = $ 13 TeV and constraints on anomalous quartic couplings",
                "Measurement of the cross section for electroweak production of a Z boson, a photon and two jets in proton-proton collisions at √(s) = 13 TeV and constraints on anomalous quartic couplings",
            ),
            (
                "A measurement of the Higgs boson mass in the diphoton decay channel",
                "A measurement of the Higgs boson mass in the diphoton decay channel",
            ),
            (
                "Measurement of the $\\Upsilon(\\text{1S}) $ pair production cross section and search for resonances decaying to $\\Upsilon(\\text{1S}) \\mu^{+}\\mu^{-}$ in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Measurement of the Υ(1S) pair production cross section and search for resonances decaying to Υ(1S) μ⁺μ⁻ in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for physics beyond the standard model in events with jets and two same-sign or at least three charged leptons in proton-proton collisions at $\\sqrt{s}=$ 13 TeV",
                "Search for physics beyond the standard model in events with jets and two same-sign or at least three charged leptons in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for charged Higgs bosons decaying into a top and a bottom quark in the all-jet final state of pp collisions at $\\sqrt{s}=$ 13 TeV",
                "Search for charged Higgs bosons decaying into a top and a bottom quark in the all-jet final state of pp collisions at √(s) = 13 TeV",
            ),
            (
                "Measurement of the associated production of a Z boson with charm or bottom quark jets in proton-proton collisions at $\\sqrt{s}=$ 13 TeV",
                "Measurement of the associated production of a Z boson with charm or bottom quark jets in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Measurements of dose-rate effects in the radiation damage of plastic scintillator tiles using silicon photomultipliers",
                "Measurements of dose-rate effects in the radiation damage of plastic scintillator tiles using silicon photomultipliers",
            ),
            (
                "Study of excited $\\Lambda_{\\mathrm{b}}^{0}$ states decaying to $\\Lambda_{\\mathrm{b}}^{0}\\pi^{+}\\pi^{-}$ in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Study of excited Λ⁰_b states decaying to Λ⁰_b π⁺π⁻ in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for an excited lepton that decays via a contact interaction to a lepton and two jets in proton-proton collisions at ${\\sqrt{s}} = $ 13 TeV",
                "Search for an excited lepton that decays via a contact interaction to a lepton and two jets in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "A deep neural network to search for new long-lived particles decaying to jets",
                "A deep neural network to search for new long-lived particles decaying to jets",
            ),
            (
                "Measurement of the top quark forward-backward production asymmetry and the anomalous chromoelectric and chromomagnetic moments in pp collisions at $\\sqrt{s} = $ 13 TeV",
                "Measurement of the top quark forward-backward production asymmetry and the anomalous chromoelectric and chromomagnetic moments in pp collisions at √(s) = 13 TeV",
            ),
            (
                "Search for direct top squark pair production in events with one lepton, jets, and missing transverse momentum at 13 TeV with the CMS experiment",
                "Search for direct top squark pair production in events with one lepton, jets, and missing transverse momentum at 13 TeV with the CMS experiment",
            ),
            (
                "Measurement of the ${\\chi_{\\mathrm{c}1}}$ and ${\\chi_{\\mathrm{c}2}}$ polarizations in proton-proton collisions at $\\sqrt{s} = $ 8 TeV",
                "Measurement of the χ_c1 and χ_c2 polarizations in proton-proton collisions at √(s) = 8 TeV",
            ),
            (
                "Extraction and validation of a new set of CMS PYTHIA-8 tunes from underlying-event measurements",
                "Extraction and validation of a new set of CMS PYTHIA-8 tunes from underlying-event measurements",
            ),
            (
                "Search for new physics in top quark production in dilepton final states in proton-proton collisions at $\\sqrt{s}$ = 13 TeV",
                "Search for new physics in top quark production in dilepton final states in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for a low-mass $\\tau^{-}\\tau^{+}$ resonance in association with a bottom quark in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Search for a low-mass τ⁻τ⁺ resonance in association with a bottom quark in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for supersymmetry in final states with photons and missing transverse momentum in proton-proton collisions at 13 TeV",
                "Search for supersymmetry in final states with photons and missing transverse momentum in proton-proton collisions at 13 TeV",
            ),
            (
                "Constraints on anomalous HVV couplings from the production of Higgs bosons decaying to $\\tau$ lepton pairs",
                "Constraints on anomalous HVV couplings from the production of Higgs bosons decaying to τ lepton pairs",
            ),
            (
                "Performance of missing transverse momentum reconstruction in proton-proton collisions at $\\sqrt{s} = $ 13 TeV using the CMS detector",
                "Performance of missing transverse momentum reconstruction in proton-proton collisions at √(s) = 13 TeV using the CMS detector",
            ),
            (
                "Search for charged Higgs bosons in the $\\mathrm{H}^{\\pm} \\to \\tau^{\\pm}\\nu_\\tau$ decay channel in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Search for charged Higgs bosons in the H^± → τ^±ν_τ decay channel in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Measurement of electroweak production of a W boson in association with two jets in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Measurement of electroweak production of a W boson in association with two jets in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "An embedding technique to determine $\\tau\\tau$ backgrounds in proton-proton collision data",
                "An embedding technique to determine ττ backgrounds in proton-proton collision data",
            ),
            (
                "Search for a heavy pseudoscalar boson decaying to a Z and a Higgs boson at $\\sqrt{s} = $ 13 TeV",
                "Search for a heavy pseudoscalar boson decaying to a Z and a Higgs boson at √(s) = 13 TeV",
            ),
            (
                "Combinations of single-top-quark production cross-section measurements and $|f_{\\rm LV}V_{tb}|$ determinations at $\\sqrt{s}=7$ and 8 TeV with the ATLAS and CMS experiments",
                "Combinations of single-top-quark production cross-section measurements and |f_LVV_tb| determinations at √(s) = 7 and 8 TeV with the ATLAS and CMS experiments",
            ),
            (
                "Azimuthal separation in nearly back-to-back jet topologies in inclusive 2- and 3-jet events in pp collisions at $\\sqrt{s}=$ 13 TeV",
                "Azimuthal separation in nearly back-to-back jet topologies in inclusive 2- and 3-jet events in pp collisions at √(s) = 13 TeV",
            ),
            (
                "Pseudorapidity distributions of charged hadrons in xenon-xenon collisions at ${\\sqrt {\\smash [b]{s_{_{\\mathrm {NN}}}}}} = $ 5.44 TeV",
                "Pseudorapidity distributions of charged hadrons in xenon-xenon collisions at √(s_NN) = 5.44 TeV",
            ),
            (
                "Measurement of exclusive $\\rho(770)^{0}$ photoproduction in ultraperipheral pPb collisions at ${\\sqrt {\\smash [b]{s_{_{\\mathrm {NN}}}}}} = $ 5.02 TeV",
                "Measurement of exclusive ρ⁰(770) photoproduction in ultraperipheral pPb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Observation of two excited $ \\mathrm{B^{+}_{c}} $ states and measurement of the ${\\mathrm{B^{+}_{c}} \\text{(2S)}}$ mass in pp collisions at $\\sqrt{s} = $ 13 TeV",
                "Observation of two excited B⁺_c states and measurement of the B⁺_c (2S) mass in pp collisions at √(s) = 13 TeV",
            ),
            (
                "Search for W boson decays to three charged pions",
                "Search for W boson decays to three charged pions",
            ),
            (
                "Charged-particle angular correlations in XeXe collisions at ${\\sqrt {\\smash [b]{s_{_{\\mathrm {NN}}}}}} = $ 5.44 TeV",
                "Charged-particle angular correlations in XeXe collisions at √(s_NN) = 5.44 TeV",
            ),
            (
                "Search for supersymmetry in events with a photon, jets, b-jets, and missing transverse momentum in proton-proton collisions at 13 TeV",
                "Search for supersymmetry in events with a photon, jets, b-jets, and missing transverse momentum in proton-proton collisions at 13 TeV",
            ),
            (
                "Measurement of electroweak WZ boson production and search for new physics in WZ + two jets events in pp collisions at $\\sqrt{s} = $ 13 TeV",
                "Measurement of electroweak WZ boson production and search for new physics in WZ + two jets events in pp collisions at √(s) = 13 TeV",
            ),
            (
                "Measurements of the ${{\\mathrm{p}}{\\mathrm{p}}\\to\\mathrm{W}\\mathrm{Z}}$  inclusive and differential production cross section and constraints on charged anomalous triple gauge couplings at ${\\sqrt{s}}  = $ 13 TeV",
                "Measurements of the pp → WZ inclusive and differential production cross section and constraints on charged anomalous triple gauge couplings at √(s) = 13 TeV",
            ),
            (
                "Search for dark matter produced in association with a single top quark or a top quark pair in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Search for dark matter produced in association with a single top quark or a top quark pair in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for the pair production of light top squarks in the $\\mathrm{e}^{\\pm}\\mu^{\\mp}$ final state in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Search for the pair production of light top squarks in the e^±μ^∓ final state in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Measurements of the Higgs boson width and anomalous HVV couplings from on-shell  and off-shell  production in the four-lepton final state",
                "Measurements of the Higgs boson width and anomalous HVV couplings from on-shell and off-shell production in the four-lepton final state",
            ),
            (
                "Measurement of the $ \\mathrm{t\\bar{t}} $ production cross section, the top quark mass, and the strong coupling constant using dilepton events in pp collisions at $\\sqrt{s} = $ 13 TeV",
                "Measurement of the tt̅ production cross section, the top quark mass, and the strong coupling constant using dilepton events in pp collisions at √(s) = 13 TeV",
            ),
            (
                "Measurement of the differential Drell-Yan cross section in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Measurement of the differential Drell-Yan cross section in proton-proton collisions at √(s) = 13 TeV",
            ),
            # CMS cms_pas_feed
            (
                "Measurements of differential Higgs boson production cross sections in the leptonic WW decay mode at $\\sqrt{s} = 13~\\mathrm{TeV}$",
                "Measurements of differential Higgs boson production cross sections in the leptonic WW decay mode at √(s) = 13 TeV",
            ),
            (
                "A measurement of the Higgs boson mass in the diphoton decay channel",
                "A measurement of the Higgs boson mass in the diphoton decay channel",
            ),
            (
                "A deep neural network for simultaneous estimation of b quark energy and resolution",
                "A deep neural network for simultaneous estimation of b quark energy and resolution",
            ),
            (
                "Template measurement of the top quark forward-backward asymmetry and anomalous chromoelectric and chromomagnetic moments in the semileptonic channel at sqrt(s)=13 TeV",
                "Template measurement of the top quark forward-backward asymmetry and anomalous chromoelectric and chromomagnetic moments in the semileptonic channel at sqrt(s) = 13 TeV",
            ),
            (
                "Search for supersymmetry in pp collisions at $\\sqrt{s}=13~\\mathrm{TeV}$ with $137~\\mathrm{fb}^{-1}$ in the final state with a single lepton using the sum of masses of large-radius jets",
                "Search for supersymmetry in pp collisions at √(s) = 13 TeV with 137 fb⁻¹ in the final state with a single lepton using the sum of masses of large-radius jets",
            ),
            (
                "Measurement of the top quark pair production cross section in the dilepton channel including a $\\tau$ lepton in proton-proton collisions at $\\sqrt{s}=13~\\mathrm{TeV}$",
                "Measurement of the top quark pair production cross section in the dilepton channel including a τ lepton in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for a narrow resonance decaying to a pair of muons in proton-proton collisions at 13 TeV",
                "Search for a narrow resonance decaying to a pair of muons in proton-proton collisions at 13 TeV",
            ),
            (
                "Observation of the $\\Lambda_{\\mathrm{b}} \\to \\mathrm{J}/\\psi \\Lambda \\phi$ decay in proton-proton collisions at $\\sqrt{s}=$ 13 TeV",
                "Observation of the Λ_b → J/ψΛϕ decay in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Measurement of properties of Bs0 to mu+mu- decays and search for B0 to mu+mu- with the CMS experiment",
                "Measurement of properties of Bs0 to mu+mu- decays and search for B0 to mu+mu- with the CMS experiment",
            ),
            (
                "Search for supersymmetry with a compressed mass spectrum in events with a soft $\\tau$ lepton, a highly energetic jet, and large missing transverse momentum in proton-proton collisions at $\\sqrt{s}=13~\\mathrm{TeV}$",
                "Search for supersymmetry with a compressed mass spectrum in events with a soft τ lepton, a highly energetic jet, and large missing transverse momentum in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Measurement of the cross section for $\\mathrm{t}\\bar{\\mathrm{t}}$ production with additional jets and b jets in proton-proton collisions at $\\sqrt{s}=13~\\mathrm{TeV}$",
                "Measurement of the cross section for tt̅ production with additional jets and b jets in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for a narrow resonance in high-mass dilepton final states in proton-proton collisions using 140$~\\mathrm{fb}^{-1}$ of data at $\\sqrt{s}=13~\\mathrm{TeV}$",
                "Search for a narrow resonance in high-mass dilepton final states in proton-proton collisions using 140 fb⁻¹ of data at √(s) = 13 TeV",
            ),
            (
                "Search for dijet resonances in events with three jets from proton-proton collisions at $\\sqrt{s}=13~\\mathrm{TeV}$",
                "Search for dijet resonances in events with three jets from proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "First measurement of the running of the top quark mass",
                "First measurement of the running of the top quark mass",
            ),
            (
                "Measurement of the associated production of a Z boson with charm or bottom quark jets in proton-proton collisions at $\\sqrt{s}=13~\\mathrm{TeV}$",
                "Measurement of the associated production of a Z boson with charm or bottom quark jets in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Machine learning-based identification of highly Lorentz-boosted hadronically decaying particles at the CMS experiment",
                "Machine learning-based identification of highly Lorentz-boosted hadronically decaying particles at the CMS experiment",
            ),
            (
                "Pileup mitigation at CMS in 13 TeV data",
                "Pileup mitigation at CMS in 13 TeV data",
            ),
            (
                "Search for the standard model Higgs boson decaying to charm quarks",
                "Search for the standard model Higgs boson decaying to charm quarks",
            ),
            (
                "Measurement of the jet mass distribution in highly boosted top quark decays in pp collisions at $\\sqrt{s}=13~\\text{TeV}$",
                "Measurement of the jet mass distribution in highly boosted top quark decays in pp collisions at √(s) = 13 TeV",
            ),
            (
                "Search for the resonant production of a pair of Higgs bosons decaying to the bb-barZZ final state",
                "Search for the resonant production of a pair of Higgs bosons decaying to the bb-barZZ final state",
            ),
            (
                "Measurement of the dependence  of inclusive jet production cross sections on the anti- $k_{\\mathrm{T}}$ distance parameter in proton-proton collisions at sqrt(s) 13 TeV",
                "Measurement of the dependence of inclusive jet production cross sections on the anti- k_T distance parameter in proton-proton collisions at sqrt(s) 13 TeV",
            ),
            (
                "Measurement of electroweak production of Z gamma in association with two jets in proton-proton collisions at sqrt(s) = 13 TeV",
                "Measurement of electroweak production of Z gamma in association with two jets in proton-proton collisions at sqrt(s) = 13 TeV",
            ),
            (
                "Measurement of the associated production of a W boson and a charm quark at $\\sqrt{s}=8~\\mathrm{TeV}$",
                "Measurement of the associated production of a W boson and a charm quark at √(s) = 8 TeV",
            ),
            (
                "Search for direct top squark pair production in events with one lepton, jets and missing transverse energy at 13 TeV",
                "Search for direct top squark pair production in events with one lepton, jets and missing transverse energy at 13 TeV",
            ),
            (
                "A search for dijet resonances in proton-proton collisions at $\\sqrt{s}=13~\\mathrm{TeV}$ with a new background prediction method",
                "A search for dijet resonances in proton-proton collisions at √(s) = 13 TeV with a new background prediction method",
            ),
            # CMS cms_paper_feed
            (
                "Bose-Einstein correlations of charged hadrons in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Bose-Einstein correlations of charged hadrons in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Mixed higher-order anisotropic flow and nonlinear response coefficients of charged particles in PbPb collisions at ${\\sqrt {\\smash [b]{s_{_{\\mathrm {NN}}}}}} = $ 2.76 and 5.02 TeV",
                "Mixed higher-order anisotropic flow and nonlinear response coefficients of charged particles in PbPb collisions at √(s_NN) = 2.76 and 5.02 TeV",
            ),
            (
                "Strange hadron production in pp and pPb collisions at ${\\sqrt {\\smash [b]{s_{_{\\mathrm {NN}}}}}} = $ 5.02 TeV",
                "Strange hadron production in pp and pPb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Study of $\\mathrm{J}/\\psi$ meson production from jet fragmentation in pp collisions at $\\sqrt{s} = $ 8 TeV",
                "Study of J/ψ meson production from jet fragmentation in pp collisions at √(s) = 8 TeV",
            ),
            (
                "Search for supersymmetry with a compressed mass spectrum in events with a soft $\\tau$ lepton, a highly energetic jet, and large missing transverse momentum in proton-proton collisions at $\\sqrt{s} =$ 13 TeV",
                "Search for supersymmetry with a compressed mass spectrum in events with a soft τ lepton, a highly energetic jet, and large missing transverse momentum in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Calibration of the CMS hadron calorimeters using proton-proton collision data at $\\sqrt{s} = $ 13 TeV",
                "Calibration of the CMS hadron calorimeters using proton-proton collision data at √(s) = 13 TeV",
            ),
            (
                "Running of the top quark mass from proton-proton collisions at ${\\sqrt{s}} = $ 13 TeV",
                "Running of the top quark mass from proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Evidence for WW production from double-parton interactions in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Evidence for WW production from double-parton interactions in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for long-lived particles using delayed photons in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Search for long-lived particles using delayed photons in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Measurement of the $\\mathrm{t\\bar{t}}\\mathrm{b\\bar{b}}$ production cross section in the all-jet final state in pp collisions at $\\sqrt{s} = $ 13 TeV",
                "Measurement of the tt̅bb̅ production cross section in the all-jet final state in pp collisions at √(s) = 13 TeV",
            ),
            (
                "Search for electroweak production of a vector-like T quark using fully hadronic final states",
                "Search for electroweak production of a vector-like T quark using fully hadronic final states",
            ),
            (
                "Measurements of differential Z boson production cross sections in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Measurements of differential Z boson production cross sections in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for low mass vector resonances decaying into quark-antiquark pairs in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Search for low mass vector resonances decaying into quark-antiquark pairs in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Searches for physics beyond the standard model with the ${M_{\\mathrm{T2}}}$ variable in hadronic final states with and without disappearing tracks in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Searches for physics beyond the standard model with the M_T2 variable in hadronic final states with and without disappearing tracks in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for a charged Higgs boson decaying into top and bottom quarks in proton-proton collisions at $\\sqrt{s} = $ 13 TeV in events with electrons or muons",
                "Search for a charged Higgs boson decaying into top and bottom quarks in proton-proton collisions at √(s) = 13 TeV in events with electrons or muons",
            ),
            (
                "Search for supersymmetry using Higgs boson to diphoton decays at $\\sqrt{s} = $ 13 TeV",
                "Search for supersymmetry using Higgs boson to diphoton decays at √(s) = 13 TeV",
            ),
            (
                "Search for production of four top quarks in final states with same-sign or multiple leptons in proton-proton collisions at $\\sqrt{s}= $ 13 TeV",
                "Search for production of four top quarks in final states with same-sign or multiple leptons in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for supersymmetry in proton-proton collisions at 13 TeV in final states with jets and missing transverse momentum",
                "Search for supersymmetry in proton-proton collisions at 13 TeV in final states with jets and missing transverse momentum",
            ),
            (
                "Search for dark photons in decays of Higgs bosons produced in association with Z bosons in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Search for dark photons in decays of Higgs bosons produced in association with Z bosons in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for dark matter particles produced in association with a Higgs boson in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Search for dark matter particles produced in association with a Higgs boson in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for heavy Higgs bosons decaying to a top quark pair in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Search for heavy Higgs bosons decaying to a top quark pair in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for direct pair production of supersymmetric partners to the $\\tau$ lepton in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Search for direct pair production of supersymmetric partners to the τ lepton in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Measurement of top quark pair production in association with a Z boson in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Measurement of top quark pair production in association with a Z boson in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Search for anomalous triple gauge couplings in WW and WZ production in lepton + jet events in proton-proton collisions at $\\sqrt{s} = $ 13 TeV",
                "Search for anomalous triple gauge couplings in WW and WZ production in lepton + jet events in proton-proton collisions at √(s) = 13 TeV",
            ),
            # ATLAS atlas_conf_feed
            (
                "Search for bottom-squark pair production with the ATLAS detector in final states containing Higgs bosons, $b$-jets and missing transverse momentum",
                "Search for bottom-squark pair production with the ATLAS detector in final states containing Higgs bosons, b-jets and missing transverse momentum",
            ),
            (
                "Search for heavy neutral Higgs bosons produced in association with $b$-quarks and decaying to $b$-quarks at $\\sqrt{s}=13$~TeV with the ATLAS detector",
                "Search for heavy neutral Higgs bosons produced in association with b-quarks and decaying to b-quarks at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Measurement of the CP violation phase $\\phi_{s}$ in $B_{s}\\to J/\\psi \\phi$ decays in ATLAS at 13 TeV",
                "Measurement of the CP violation phase ϕ_s in B_s → J/ψϕ decays in ATLAS at 13 TeV",
            ),
            (
                "Search for electroweak production of charginos and sleptons decaying in final states with two leptons and missing transverse momentum in $\\sqrt{s}=13$ TeV $pp$ collisions using the ATLAS detector",
                "Search for electroweak production of charginos and sleptons decaying in final states with two leptons and missing transverse momentum in √(s) = 13 TeV pp collisions using the ATLAS detector",
            ),
            (
                "Search for New Phenomena in Dijet Events using 139 fb$^{−1}$ of $pp$ collisions at $\\sqrt{s}$ = 13TeV collected with the ATLAS Detector",
                "Search for New Phenomena in Dijet Events using 139 fb^−1 of pp collisions at √(s) = 13 TeV collected with the ATLAS Detector",
            ),
            (
                "Search for long-lived, massive particles in events with a displaced vertex and a displaced muon in $pp$ collisions at $\\sqrt{s} = 13$ TeV with the ATLAS detector",
                "Search for long-lived, massive particles in events with a displaced vertex and a displaced muon in pp collisions at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Combined measurements of Higgs boson production and decay using up to $80$ fb$^{-1}$ of proton--proton collision data at $\\sqrt{s}=$ 13 TeV collected with the ATLAS experiment",
                "Combined measurements of Higgs boson production and decay using up to 80 fb⁻¹ of proton–proton collision data at √(s) = 13 TeV collected with the ATLAS experiment",
            ),
            (
                "Measurement of Higgs boson production in association with a $t\\overline t$ pair in the diphoton decay channel using 139~fb$^{-1}$ of LHC data collected at $\\sqrt{s} = 13$~TeV by the ATLAS experiment",
                "Measurement of Higgs boson production in association with a tt pair in the diphoton decay channel using 139 fb⁻¹ of LHC data collected at √(s) = 13 TeV by the ATLAS experiment",
            ),
            (
                "Search for diboson resonances in hadronic final states in 139 fb$^{-1}$ of $pp$ collisions at $\\sqrt{s} = 13$ TeV with the ATLAS detector",
                "Search for diboson resonances in hadronic final states in 139 fb⁻¹ of pp collisions at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Observation of light-by-light scattering in ultraperipheral Pb+Pb collisions with the ATLAS detector",
                "Observation of light-by-light scattering in ultraperipheral Pb+Pb collisions with the ATLAS detector",
            ),
            (
                "Search for high-mass dilepton resonances using $139\\,\\mathrm{fb}^{-1}$ of $pp$ collision data collected at $\\sqrt{s}=13\\,\\mathrm{TeV}$ with the ATLAS detector",
                "Search for high-mass dilepton resonances using 139 fb⁻¹ of pp collision data collected at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Calibration of the $b$-tagging eﬃciency on charm jets using a sample of $W$+$c$ events with $\\sqrt{s}$ = 13 TeV ATLAS data",
                "Calibration of the b-tagging eﬃciency on charm jets using a sample of W+c events with √(s) = 13 TeV ATLAS data",
            ),
            (
                "Combination of searches for invisible Higgs boson decays with the ATLAS experiment",
                "Combination of searches for invisible Higgs boson decays with the ATLAS experiment",
            ),
            (
                "Measurements of $VH$, $H \\to b\\bar{b}$ production as a function of the vector boson transverse momentum in 13 TeV pp collisions with the ATLAS detector",
                "Measurements of VH, H → bb̅ production as a function of the vector boson transverse momentum in 13 TeV pp collisions with the ATLAS detector",
            ),
            (
                "Search for boosted resonances decaying to two b-quarks and produced in association with a jet at $\\sqrt{s}=13$ TeV with the ATLAS detector",
                "Search for boosted resonances decaying to two b-quarks and produced in association with a jet at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Constraints on mediator-based dark matter models using $\\sqrt s = 13$ TeV $pp$ collisions at the LHC with the ATLAS detector",
                "Constraints on mediator-based dark matter models using √(s) = 13 TeV pp collisions at the LHC with the ATLAS detector",
            ),
            (
                "Dijet azimuthal correlations and conditional yields in $p\\!p$ and $p$+Pb collisions at $\\sqrt{s_{_\\text{NN}}}$~=~5.02 TeV with the ATLAS detector",
                "Dijet azimuthal correlations and conditional yields in pp and p+Pb collisions at √(s_NN) = 5.02 TeV with the ATLAS detector",
            ),
            (
                "Search for top quark decays t\\rightarrowHq with 36 fb^{−1} of pp collision data at \\sqrt{s} = 13 TeV with the ATLAS detector",
                "Search for top quark decays t → Hq with 36 fb^−1 of pp collision data at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Measurements of inclusive and differential cross-sections of $t\\bar{t}\\gamma$ production in leptonic final states in a fiducial volume at $\\sqrt{s}=13~\\text{TeV}$ in ATLAS",
                "Measurements of inclusive and differential cross-sections of tt̅γ production in leptonic final states in a fiducial volume at √(s) = 13 TeV in ATLAS",
            ),
            (
                "Measurement of the $t\\bar{t}W$ and $t\\bar{t}Z$ cross sections in proton–proton collisions at $\\sqrt{s}$ = 13 TeV with the ATLAS detector",
                "Measurement of the tt̅W and tt̅Z cross sections in proton–proton collisions at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Study of the rare decays of B0s and B0 into muon pairs from data collected during 2015 and 2016 with the ATLAS detector",
                "Study of the rare decays of B0s and B0 into muon pairs from data collected during 2015 and 2016 with the ATLAS detector",
            ),
            (
                "Calibration of the ATLAS $b$-tagging algorithm in $t\\bar{t}$ semi-leptonic events",
                "Calibration of the ATLAS b-tagging algorithm in tt̅ semi-leptonic events",
            ),
            (
                "Search for charged lepton-flavour violation in top-quark decays at the LHC with the ATLAS detector",
                "Search for charged lepton-flavour violation in top-quark decays at the LHC with the ATLAS detector",
            ),
            (
                "Combination of searches for Higgs boson pairs in $pp$ collisions at 13 TeV with the ATLAS experiment.",
                "Combination of searches for Higgs boson pairs in pp collisions at 13 TeV with the ATLAS experiment.",
            ),
            (
                "Search for direct chargino pair production with W-boson mediated decays in events with two leptons and missing transverse momentum at $\\sqrt{s} = 13$ TeV with the ATLAS detector",
                "Search for direct chargino pair production with W-boson mediated decays in events with two leptons and missing transverse momentum at √(s) = 13 TeV with the ATLAS detector",
            ),
            # ATLAS atlas_paper_feed
            (
                "Observation of light-by-light scattering in ultraperipheral Pb+Pb collisions with the ATLAS detector",
                "Observation of light-by-light scattering in ultraperipheral Pb+Pb collisions with the ATLAS detector",
            ),
            (
                "Evidence for the production of three massive vector bosons with the ATLAS detector",
                "Evidence for the production of three massive vector bosons with the ATLAS detector",
            ),
            (
                "Measurement of the production cross section for a Higgs boson in association with a vector boson in the $H \\rightarrow WW^{\\ast} \\rightarrow \\ell\\nu\\ell\\nu$ channel in $pp$ collisions at $\\sqrt{s} = 13$ TeV with the ATLAS detector",
                "Measurement of the production cross section for a Higgs boson in association with a vector boson in the H → WW^∗ → ℓνℓν channel in pp collisions at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Measurements of top-quark pair spin correlations in the $e\\mu$ channel at $\\sqrt{s} = 13$ TeV using $pp$ collisions in the ATLAS detector",
                "Measurements of top-quark pair spin correlations in the eμ channel at √(s) = 13 TeV using pp collisions in the ATLAS detector",
            ),
            (
                "Search for high-mass dilepton resonances using 139 fb$^{-1}$ of $pp$ collision data collected at $\\sqrt{s}=13$ TeV with the ATLAS detector",
                "Search for high-mass dilepton resonances using 139 fb⁻¹ of pp collision data collected at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Measurement of $VH$, $H\\to b\\bar{b}$ production as a function of the vector-boson transverse momentum in 13 TeV $pp$ collisions with the ATLAS detector",
                "Measurement of VH, H → bb̅ production as a function of the vector-boson transverse momentum in 13 TeV pp collisions with the ATLAS detector",
            ),
            (
                "Measurement of jet-substructure observables in top quark, $W$ boson and light jet production in proton-proton collisions at $\\sqrt{s}=13$ TeV with the ATLAS detector",
                "Measurement of jet-substructure observables in top quark, W boson and light jet production in proton-proton collisions at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Measurement of prompt photon production in $\\sqrt{s_\\mathrm{NN}} = 8.16$ TeV $p$+Pb collisions with ATLAS",
                "Measurement of prompt photon production in √(s_NN) = 8.16 TeV p+Pb collisions with ATLAS",
            ),
            (
                "Constraints on mediator-based dark matter and scalar dark energy models using $\\sqrt{s}= 13$ TeV $pp$ collision data collected by the ATLAS detector",
                "Constraints on mediator-based dark matter and scalar dark energy models using √(s) = 13 TeV pp collision data collected by the ATLAS detector",
            ),
            (
                "Search for heavy particles decaying into a top-quark pair in the fully hadronic final state in $pp$ collisions at $\\sqrt{s} =$13 TeV with the ATLAS detector",
                "Search for heavy particles decaying into a top-quark pair in the fully hadronic final state in pp collisions at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Comparison of fragmentation functions for light-quark- and gluon-dominated jets from $pp$ and Pb+Pb collisions in ATLAS",
                "Comparison of fragmentation functions for light-quark- and gluon-dominated jets from pp and Pb+Pb collisions in ATLAS",
            ),
            (
                "Searches for third-generation scalar leptoquarks in $\\sqrt{s} = 13$ TeV $pp$ collisions with the ATLAS detector",
                "Searches for third-generation scalar leptoquarks in √(s) = 13 TeV pp collisions with the ATLAS detector",
            ),
            (
                "Combinations of single-top-quark production cross-section measurements and $|f_{\\rm LV}V_{tb}|$ determinations at $\\sqrt{s}=7$ and 8 TeV with the ATLAS and CMS experiments",
                "Combinations of single-top-quark production cross-section measurements and |f_LVV_tb| determinations at √(s) = 7 and 8 TeV with the ATLAS and CMS experiments",
            ),
            (
                "Measurement of the four-lepton invariant mass spectrum in 13 TeV proton-proton collisions with the ATLAS detector",
                "Measurement of the four-lepton invariant mass spectrum in 13 TeV proton-proton collisions with the ATLAS detector",
            ),
            (
                "Measurement of $W^{\\pm}Z$ production cross sections and gauge boson polarisation in $pp$ collisions at $\\sqrt{s} = 13$ TeV with the ATLAS detector",
                "Measurement of W^±Z production cross sections and gauge boson polarisation in pp collisions at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Electron reconstruction and identification in the ATLAS experiment using the 2015 and 2016 LHC proton-proton collision data at $\\sqrt{s} = 13$ TeV",
                "Electron reconstruction and identification in the ATLAS experiment using the 2015 and 2016 LHC proton-proton collision data at √(s) = 13 TeV",
            ),
            (
                "Search for long-lived neutral particles in $pp$ collisions at $\\sqrt{s} = 13$ TeV that decay into displaced hadronic jets in the ATLAS calorimeter",
                "Search for long-lived neutral particles in pp collisions at √(s) = 13 TeV that decay into displaced hadronic jets in the ATLAS calorimeter",
            ),
            (
                "Search for heavy charged long-lived particles in the ATLAS detector in 31.6 fb$^{-1}$ of proton-proton collision data at $\\sqrt{s} = 13$ TeV",
                "Search for heavy charged long-lived particles in the ATLAS detector in 31.6 fb⁻¹ of proton-proton collision data at √(s) = 13 TeV",
            ),
            (
                "Searches for scalar leptoquarks and differential cross-section measurements in dilepton-dijet events in proton-proton collisions at a centre-of-mass energy of $\\sqrt{s} = 13$ TeV with the ATLAS experiment",
                "Searches for scalar leptoquarks and differential cross-section measurements in dilepton-dijet events in proton-proton collisions at a centre-of-mass energy of √(s) = 13 TeV with the ATLAS experiment",
            ),
            (
                "Search for low-mass resonances decaying into two jets and produced in association with a photon using $pp$ collisions at $\\sqrt{s} = 13$ TeV with the ATLAS detector",
                "Search for low-mass resonances decaying into two jets and produced in association with a photon using pp collisions at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Dijet azimuthal correlations and conditional yields in $pp$ and $p$+Pb collisions at $\\sqrt{s_{\\rm NN}}$ = 5.02 TeV with the ATLAS detector",
                "Dijet azimuthal correlations and conditional yields in pp and p+Pb collisions at √(s_NN) = 5.02 TeV with the ATLAS detector",
            ),
            (
                "Measurement of the ratio of cross sections for inclusive isolated-photon production in $pp$ collisions at $\\sqrt{s}=13$ and $8$ TeV with the ATLAS detector",
                "Measurement of the ratio of cross sections for inclusive isolated-photon production in pp collisions at √(s) = 13 and 8 TeV with the ATLAS detector",
            ),
            (
                "Search for scalar resonances decaying into $\\mu^{+}\\mu^{-}$ in events with and without $b$-tagged jets produced in proton-proton collisions at $\\sqrt{s}=13$ TeV with the ATLAS detector",
                "Search for scalar resonances decaying into μ⁺μ⁻ in events with and without b-tagged jets produced in proton-proton collisions at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Measurement of the $t\\bar{t}Z$ and $t\\bar{t}W$ cross sections in proton-proton collisions at $\\sqrt{s}=13$ TeV with the ATLAS detector",
                "Measurement of the tt̅Z and tt̅W cross sections in proton-proton collisions at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Search for top-quark decays $t \\rightarrow Hq$ with 36 fb$^{-1}$ of $pp$ collision data at $\\sqrt{s}=13$ TeV with the ATLAS detector",
                "Search for top-quark decays t → Hq with 36 fb⁻¹ of pp collision data at √(s) = 13 TeV with the ATLAS detector",
            ),
            # ATLAS atlas_paper_feed
            (
                "Evidence for electroweak production of two jets in association with a  $Z\\gamma$ pair in $pp$ collisions at $\\sqrt{s} = 13$ TeV with the ATLAS  detector",
                "Evidence for electroweak production of two jets in association with a Zγ pair in pp collisions at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Measurement of the $t\\bar{t}$ production cross-section and lepton differential distributions in $e\\mu$ dilepton events from $pp$ collisions at $\\sqrt{s}=13$ TeV with the ATLAS detector",
                "Measurement of the tt̅ production cross-section and lepton differential distributions in eμ dilepton events from pp collisions at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Search for new resonances in mass distributions of jet pairs using 139  fb$^{-1}$ of $pp$ collisions at $\\sqrt{s}=13$ TeV with the ATLAS detector",
                "Search for new resonances in mass distributions of jet pairs using 139 fb⁻¹ of pp collisions at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Determination of jet calibration and energy resolution in proton-proton  collisions at $\\sqrt{s}$ = 8 TeV using the ATLAS detector",
                "Determination of jet calibration and energy resolution in proton-proton collisions at √(s) = 8 TeV using the ATLAS detector",
            ),
            (
                "Measurement of $J/\\psi$ production in association with a $W^\\pm$ boson with $pp$ data at 8 TeV",
                "Measurement of J/ψ production in association with a W^± boson with pp data at 8 TeV",
            ),
            (
                "Search for the Higgs boson decays $H \\to ee$ and $H \\to e\\mu$ in $pp$  collisions at $\\sqrt{s} = 13$ TeV with the ATLAS detector",
                "Search for the Higgs boson decays H → ee and H → eμ in pp collisions at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Search for direct production of electroweakinos in final states with one  lepton, missing transverse momentum and a Higgs boson decaying into two $b$-jets in $pp$ collisions at $\\sqrt{s}=13$ TeV with the ATLAS detector",
                "Search for direct production of electroweakinos in final states with one lepton, missing transverse momentum and a Higgs boson decaying into two b-jets in pp collisions at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Search for squarks and gluinos in final states with same-sign leptons  and jets using 139 fb$^{-1}$ of data collected with the ATLAS detector",
                "Search for squarks and gluinos in final states with same-sign leptons and jets using 139 fb⁻¹ of data collected with the ATLAS detector",
            ),
            (
                "Combined measurements of Higgs boson production and decay using up to $80$ fb$^{-1}$ of proton-proton collision data at $\\sqrt{s}=$ 13 TeV  collected with the ATLAS experiment",
                "Combined measurements of Higgs boson production and decay using up to 80 fb⁻¹ of proton-proton collision data at √(s) = 13 TeV collected with the ATLAS experiment",
            ),
            (
                "Measurement of azimuthal anisotropy of muons from charm and bottom  hadrons in $pp$ collisions at $\\sqrt{s}=13$ TeV with the ATLAS detector",
                "Measurement of azimuthal anisotropy of muons from charm and bottom hadrons in pp collisions at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Search for light long-lived neutral particles produced in $pp$ collisions at $\\sqrt{s} =$ 13 TeV and decaying into collimated leptons or light hadrons with the ATLAS detector",
                "Search for light long-lived neutral particles produced in pp collisions at √(s) = 13 TeV and decaying into collimated leptons or light hadrons with the ATLAS detector",
            ),
            (
                "Performance of electron and photon triggers in ATLAS during LHC Run 2",
                "Performance of electron and photon triggers in ATLAS during LHC Run 2",
            ),
            (
                "Search for flavour-changing neutral currents in processes with one top  quark and a photon using 81 fb$^{-1}$ of $pp$ collisions at $\\sqrt{s} = 13$ TeV with the ATLAS experiment",
                "Search for flavour-changing neutral currents in processes with one top quark and a photon using 81 fb⁻¹ of pp collisions at √(s) = 13 TeV with the ATLAS experiment",
            ),
            (
                "Search for electroweak production of charginos and sleptons decaying  into final states with two leptons and missing transverse momentum in  $\\sqrt{s}=13$ TeV $pp$ collisions using the ATLAS detector",
                "Search for electroweak production of charginos and sleptons decaying into final states with two leptons and missing transverse momentum in √(s) = 13 TeV pp collisions using the ATLAS detector",
            ),
            (
                "Measurements of top-quark pair differential and double-differential  cross-sections in the $\\ell$+jets channel with $pp$ collisions at  $\\sqrt{s}=13$ TeV using the ATLAS detector",
                "Measurements of top-quark pair differential and double-differential cross-sections in the ℓ+jets channel with pp collisions at √(s) = 13 TeV using the ATLAS detector",
            ),
            (
                "Search for non-resonant Higgs boson pair production in the  $bb\\ell\\nu\\ell\\nu$ final state with the ATLAS detector in $pp$ collisions at $\\sqrt{s} = 13$ TeV",
                "Search for non-resonant Higgs boson pair production in the bbℓνℓν final state with the ATLAS detector in pp collisions at √(s) = 13 TeV",
            ),
            (
                "Measurement of angular and momentum distributions of charged particles within and around jets in Pb+Pb and $pp$ collisions at $\\sqrt{s_{\\mathrm{NN}}} = 5.02$ TeV with the ATLAS detector",
                "Measurement of angular and momentum distributions of charged particles within and around jets in Pb+Pb and pp collisions at √(s_NN) = 5.02 TeV with the ATLAS detector",
            ),
            (
                "Search for bottom-squark pair production with the ATLAS detector in final states containing Higgs bosons, $b$-jets and missing transverse momentum",
                "Search for bottom-squark pair production with the ATLAS detector in final states containing Higgs bosons, b-jets and missing transverse momentum",
            ),
            (
                "Measurement of the inclusive isolated-photon cross section in $pp$  collisions at $\\sqrt{s}=13$ TeV using 36 fb$^{-1}$ of ATLAS data",
                "Measurement of the inclusive isolated-photon cross section in pp collisions at √(s) = 13 TeV using 36 fb⁻¹ of ATLAS data",
            ),
            (
                "Electron and photon performance measurements with the ATLAS detector using the 2015-2017 LHC proton-proton collision data",
                "Electron and photon performance measurements with the ATLAS detector using the 2015-2017 LHC proton-proton collision data",
            ),
            (
                "Measurement of $K_S^0$ and $\\Lambda^0$ production in $t \\bar{t}$ dileptonic events in $pp$ collisions at $\\sqrt{s} =$ 7 TeV with the ATLAS detector",
                "Measurement of K⁰_S and Λ⁰ production in tt̅ dileptonic events in pp collisions at √(s) = 7 TeV with the ATLAS detector",
            ),
            (
                "Measurement of $W^\\pm$ boson production in Pb+Pb collisions at  $\\sqrt{s_\\mathrm{NN}} = 5.02$ TeV with the ATLAS detector",
                "Measurement of W^± boson production in Pb+Pb collisions at √(s_NN) = 5.02 TeV with the ATLAS detector",
            ),
            (
                "Search for displaced vertices of oppositely charged leptons from decays of long-lived particles in $pp$ collisions at $\\sqrt{s}$ = 13 TeV with the ATLAS detector",
                "Search for displaced vertices of oppositely charged leptons from decays of long-lived particles in pp collisions at √(s) = 13 TeV with the ATLAS detector",
            ),
            (
                "Measurement of the jet mass in high transverse momentum $Z(\\rightarrow b\\overline{b})\\gamma$ production at $\\sqrt{s}= 13$ TeV using the ATLAS detector",
                "Measurement of the jet mass in high transverse momentum Z( → bb)γ production at √(s) = 13 TeV using the ATLAS detector",
            ),
            (
                "Measurement of the inclusive cross-section for the production of jets in association with a $Z$ boson in proton-proton collisions at 8 TeV using the ATLAS detector",
                "Measurement of the inclusive cross-section for the production of jets in association with a Z boson in proton-proton collisions at 8 TeV using the ATLAS detector",
            ),
            # ALICE alice_paper_feed
            (
                "One-dimensional charged kaon femtoscopy in p-Pb collisions at $\\sqrt{s_{\\rm NN}}$ = 5.02 TeV",
                "One-dimensional charged kaon femtoscopy in p-Pb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Investigations of anisotropic flow using multi-particle azimuthal correlations in pp, p$-$Pb, Xe$-$Xe, and Pb$-$Pb collisions at the LHC",
                "Investigations of anisotropic flow using multi-particle azimuthal correlations in pp, p-Pb, Xe-Xe, and Pb-Pb collisions at the LHC",
            ),
            (
                "Multiplicity dependence of (anti-)deuteron production in pp collisions at $\\sqrt{s}$  = 7 TeV",
                "Multiplicity dependence of (anti-)deuteron production in pp collisions at √(s) = 7 TeV",
            ),
            (
                "Calibration of the photon spectrometer PHOS of the ALICE experiment",
                "Calibration of the photon spectrometer PHOS of the ALICE experiment",
            ),
            (
                "Measurement of D$^0$, D$^+$, D$^*$ and D$_s$ production in pp collisions at  $\\sqrt{s}$ = 5.02 TeV",
                "Measurement of D⁰, D⁺, D* and D_s production in pp collisions at √(s) = 5.02 TeV",
            ),
            (
                "Real-time data processing in the ALICE High Level Trigger at the LHC",
                "Real-time data processing in the ALICE High Level Trigger at the LHC",
            ),
            (
                "Event-shape and multiplicity dependence of freeze-out radii in pp collisions at $\\sqrt{s}$ = 7 TeV",
                "Event-shape and multiplicity dependence of freeze-out radii in pp collisions at √(s) = 7 TeV",
            ),
            (
                "Study of J/$\\psi$ azimuthal anisotropy at forward rapidity in Pb-Pb collisions at $\\sqrt{s_{\\rm NN}}$ = 5.02 TeV",
                "Study of J/ψ azimuthal anisotropy at forward rapidity in Pb-Pb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Charged-particle pseudorapidity density at mid-rapidity in p-Pb collisions at $\\sqrt{s_{\\rm{NN}}}$ = 8.16 TeV",
                "Charged-particle pseudorapidity density at mid-rapidity in p-Pb collisions at √(s_NN) = 8.16 TeV",
            ),
            (
                "Jet fragmentation transverse momentum measurements from di-hadron correlations in $\\sqrt{s}$ = 7 TeV pp and $\\sqrt{s_{\\rm{NN}}}$ = 5.02 TeV p-Pb collisions",
                "Jet fragmentation transverse momentum measurements from di-hadron correlations in √(s) = 7 TeV pp and √(s_NN) = 5.02 TeV p-Pb collisions",
            ),
            (
                "$\\Lambda_{\\rm c}^{+}$ production in Pb-Pb collisions at $\\sqrt{s_{\\rm NN}}=5.02$ TeV",
                "Λ⁺_c production in Pb-Pb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Event-shape engineering for the D-meson elliptic flow in mid-central Pb-Pb collisions at $\\sqrt{s_{\\rm NN}}=5.02$ TeV",
                "Event-shape engineering for the D-meson elliptic flow in mid-central Pb-Pb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Energy dependence of exclusive $J/\\psi$ photoproduction off protons in ultra-peripheral p-Pb collisions at $\\sqrt{s_{\\rm{NN}}}$ = 5.02 TeV",
                "Energy dependence of exclusive J/ψ photoproduction off protons in ultra-peripheral p-Pb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Charged jet cross section and fragmentation in proton-proton collisions at $\\sqrt{s}$ = 7 TeV",
                "Charged jet cross section and fragmentation in proton-proton collisions at √(s) = 7 TeV",
            ),
            (
                "Measuring $\\rm{K}^{0}\\rm{K}^{\\pm}$ interactions using pp collisions at $\\sqrt{s}$ = 7 TeV",
                "Measuring K⁰K^± interactions using pp collisions at √(s) = 7 TeV",
            ),
            (
                "Multiplicity dependence of light-flavor hadron production in pp collisions at $\\sqrt{s}$ = 7 TeV",
                "Multiplicity dependence of light-flavor hadron production in pp collisions at √(s) = 7 TeV",
            ),
            (
                "Medium modification of the shape of small-radius jets in central Pb-Pb collisions at $\\sqrt{s_{\\rm{NN}}}$ = 2.76 TeV",
                "Medium modification of the shape of small-radius jets in central Pb-Pb collisions at √(s_NN) = 2.76 TeV",
            ),
            (
                "Measurement of dielectron production in central Pb-Pb collisions at $\\sqrt{{\\textit{s}}_{\\mathrm{NN}}}$ = 2.76 TeV",
                "Measurement of dielectron production in central Pb-Pb collisions at √(s_NN) = 2.76 TeV",
            ),
            (
                "p-p, p-$\\Lambda$ and $\\Lambda$-$\\Lambda$ correlations studied via femtoscopy in pp reactions at $\\sqrt{s}$ = 7 TeV",
                "p-p, p-Λ and Λ-Λ correlations studied via femtoscopy in pp reactions at √(s) = 7 TeV",
            ),
            (
                "Dielectron and heavy-quark production in inelastic and high-multiplicity proton-proton collisions at $\\sqrt{s} = 13$ TeV",
                "Dielectron and heavy-quark production in inelastic and high-multiplicity proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "Centrality and pseudorapidity dependence of the charged-particle multiplicity density in Xe-Xe collisions at $\\sqrt{s_{\\rm NN}}$ = 5.44 TeV",
                "Centrality and pseudorapidity dependence of the charged-particle multiplicity density in Xe-Xe collisions at √(s_NN) = 5.44 TeV",
            ),
            (
                "Azimuthal anisotropy of heavy-flavour decay electrons in p-Pb collisions at $\\sqrt{s_{NN}}$ = 5.02 TeV",
                "Azimuthal anisotropy of heavy-flavour decay electrons in p-Pb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Non-Flow and Flow studies with differential transverse momentum and number density correlations in p-Pb and Pb-Pb at LHC",
                "Non-Flow and Flow studies with differential transverse momentum and number density correlations in p-Pb and Pb-Pb at LHC",
            ),
            (
                "Direct photon elliptic flow in Pb-Pb collisions at $\\sqrt{s_{NN}}$ = 2.76 TeV",
                "Direct photon elliptic flow in Pb-Pb collisions at √(s_NN) = 2.76 TeV",
            ),
            (
                "Suppression of $\\Lambda(1520)$ resonance production in central Pb-Pb collisions at $\\sqrt{s_{NN}}$ = 2.76 TeV",
                "Suppression of Λ(1520) resonance production in central Pb-Pb collisions at √(s_NN) = 2.76 TeV",
            ),
            # ALICE alice_paper_feed
            (
                "Production of charged pions, kaons and (anti-)protons in Pb-Pb and inelastic pp collisions at $\\sqrt{s_{\\rm{NN}}}$ = 5.02 TeV",
                "Production of charged pions, kaons and (anti-)protons in Pb-Pb and inelastic pp collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Measurement of electrons from semileptonic heavy-flavour hadron decays  at mid-rapidity in pp and Pb-Pb collisions at $\\sqrt{s_{\\rm{NN}}}$ = 5.02 TeV",
                "Measurement of electrons from semileptonic heavy-flavour hadron decays at mid-rapidity in pp and Pb-Pb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Measurement of the (anti-)$^{3}$He elliptic flow in Pb-Pb collisions at $\\sqrt{s_{\\rm NN}}$ = 5.02 TeV",
                "Measurement of the (anti-)^3He elliptic flow in Pb-Pb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Measurements of inclusive jet spectra in pp and central Pb–Pb collisions at $\\sqrt{s_{\\rm{NN}}}$ = 5.02 TeV",
                "Measurements of inclusive jet spectra in pp and central Pb–Pb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Studies of J/$\\psi$ production at forward rapidity in Pb-Pb collisions at $\\sqrt{s_{\\rm NN}}$ = 5.02 TeV",
                "Studies of J/ψ production at forward rapidity in Pb-Pb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Measurement of $\\Lambda$(1520) production in pp collisions at $\\sqrt{s}$ = 7 TeV and p-Pb collisions at $\\sqrt{s_{\\rm{NN}}}$ = 5.02 TeV",
                "Measurement of Λ(1520) production in pp collisions at √(s) = 7 TeV and p-Pb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Global polarization of $\\Lambda$ and $\\overline{\\Lambda}$ hyperons in Pb-Pb collisions at the LHC",
                "Global polarization of Λ and Λ hyperons in Pb-Pb collisions at the LHC",
            ),
            (
                "Multiplicity dependence of (multi-)strange hadron production in proton-proton collisions at $\\sqrt{s}$ = 13 TeV",
                "Multiplicity dependence of (multi-)strange hadron production in proton-proton collisions at √(s) = 13 TeV",
            ),
            (
                "$^{3}_{\\Lambda}\\mathrm{H}$ and $^{3}_{\\overline{\\Lambda}}\\mathrm{\\overline{H}}$ lifetime measurement in Pb-Pb collisions at \\newline $\\sqrt{s_{\\mathrm{NN}}} = $ 5.02 TeV via two-body decay",
                "^3_ΛH and ^3_ΛH lifetime measurement in Pb-Pb collisions at √(s_NN) = 5.02 TeV via two-body decay",
            ),
            (
                "Measurement of Υ(1S) elliptic flow at forward rapidity in Pb-Pb collisions at $\\sqrt{s_{NN}}$ = 5.02TeV",
                "Measurement of Υ(1S) elliptic flow at forward rapidity in Pb-Pb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Measurement of prompt D$^{0}$, D$^{+}$, D$^{∗+}$,  and D$^{+}_{s}$ production in p$-$Pb collisions at $\\sqrt{s_{\\rm NN}}$ = 5.02 TeV",
                "Measurement of prompt D⁰, D⁺, D*⁺, and D⁺_s production in p-Pb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Multiplicity dependence of light (anti-)nuclei production in p-Pb collisions at $\\sqrt{s_{\\rm{NN}}}$ = 5.02 TeV",
                "Multiplicity dependence of light (anti-)nuclei production in p-Pb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Scattering studies with low-energy kaon-proton femtoscopy in proton-proton collisions at the LHC",
                "Scattering studies with low-energy kaon-proton femtoscopy in proton-proton collisions at the LHC",
            ),
            (
                "Measurement of the inclusive isolated photon production cross section in pp collisions at $\\sqrt{s}$ = 7 TeV",
                "Measurement of the inclusive isolated photon production cross section in pp collisions at √(s) = 7 TeV",
            ),
            (
                "Inclusive J/$\\psi$ production at mid-rapidity in pp collisions at $\\sqrt{s}$ = 5.02 TeV",
                "Inclusive J/ψ production at mid-rapidity in pp collisions at √(s) = 5.02 TeV",
            ),
            (
                "Study of the $\\Lambda$-$\\Lambda$ interaction  with femtoscopy correlations in pp and p-Pb collisions at the LHC",
                "Study of the Λ-Λ interaction with femtoscopy correlations in pp and p-Pb collisions at the LHC",
            ),
            (
                "Charged-particle production as a function of multiplicity and transverse spherocity in pp collisions at $\\sqrt{s} =5.02$ and 13 TeV",
                "Charged-particle production as a function of multiplicity and transverse spherocity in pp collisions at √(s) = 5.02 and 13 TeV",
            ),
            (
                "Exploration of jet substructure using iterative declustering in pp and Pb-Pb collisions at LHC energies",
                "Exploration of jet substructure using iterative declustering in pp and Pb-Pb collisions at LHC energies",
            ),
            (
                "Measurement of the production of charm jets tagged with D$^{0}$ mesons in pp collisions at $\\sqrt{s}$= 7 TeV",
                "Measurement of the production of charm jets tagged with D⁰ mesons in pp collisions at √(s) = 7 TeV",
            ),
            (
                "First observation of an attractive interaction between a proton and a multi-strange baryon",
                "First observation of an attractive interaction between a proton and a multi-strange baryon",
            ),
            (
                "Measurement of jet radial profiles in Pb$-$Pb collisions at $\\sqrt{s_{\\rm NN}}$ = 2.76 TeV",
                "Measurement of jet radial profiles in Pb-Pb collisions at √(s_NN) = 2.76 TeV",
            ),
            (
                "Production of muons from heavy-flavour hadron decays in pp collisions at $\\sqrt{s}=5.02$ TeV",
                "Production of muons from heavy-flavour hadron decays in pp collisions at √(s) = 5.02 TeV",
            ),
            (
                "Measurement of charged jet cross section in pp collisions at $\\sqrt{s}=5.02$ TeV",
                "Measurement of charged jet cross section in pp collisions at √(s) = 5.02 TeV",
            ),
            (
                "Coherent J/$\\psi$ photoproduction at forward rapidity in ultra-peripheral Pb-Pb collisions at $\\sqrt{s_{\\rm{NN}}}=5.02$ TeV",
                "Coherent J/ψ photoproduction at forward rapidity in ultra-peripheral Pb-Pb collisions at √(s_NN) = 5.02 TeV",
            ),
            # LHCb lhcb_paper_feed
            (
                "Measurements of $CP$ asymmetries in charmless four-body $\\Lambda^0_b$ and $\\Xi_b^0$ decays",
                "Measurements of CP asymmetries in charmless four-body Λ⁰_b and Ξ⁰_b decays",
            ),
            (
                "Observation of an excited $B_c^+$ state",
                "Observation of an excited B⁺_c state",
            ),
            (
                "Near-threshold $D\\bar{D}$ spectroscopy and observation of a new charmonium state",
                "Near-threshold DD̅ spectroscopy and observation of a new charmonium state",
            ),
            (
                "Search for lepton-universality violation in $B^+\\to K^+\\ell^+\\ell^-$ decays",
                "Search for lepton-universality violation in B⁺ → K⁺ℓ⁺ℓ⁻ decays",
            ),
            (
                "Observation of $C\\!P$ violation in charm decays",
                "Observation of CP violation in charm decays",
            ),
            (
                "Measurement of the $CP$-violating phase $\\phi_s$ from $B_{s}^{0}\\to J/\\psi\\pi^+\\pi⁻$ decays in 13 TeV $pp$ collisions",
                "Measurement of the CP-violating phase ϕ_s from B⁰_s → J/ψπ⁺π⁻ decays in 13 TeV pp collisions",
            ),
            (
                "Measurement of the mass difference between neutral charm-meson eigenstates",
                "Measurement of the mass difference between neutral charm-meson eigenstates",
            ),
            (
                "Search for $CP$ violation in $D^+_s\\to K_S^0\\pi^+$, $D^+\\to K_S^0K^+$ and $D^+\\to\\phi\\pi^+$ decays",
                "Search for CP violation in D⁺_s → K⁰_S π⁺, D⁺ → K⁰_S K⁺ and D⁺ → ϕπ⁺ decays",
            ),
            (
                "Amplitude analysis of $B^{0}_{s} \\rightarrow K^{0}_{\\textrm{S}} K^{\\pm}\\pi^{\\mp}$ decays",
                "Amplitude analysis of B⁰_s → K⁰_S K^±π^∓ decays",
            ),
            (
                "Measurement of $b$-hadron fractions in 13 TeV $pp$ collisions",
                "Measurement of b-hadron fractions in 13 TeV pp collisions",
            ),
            (
                "Dalitz Plot analysis of the $D^+ \\to K^- K^+ K^+$ decay",
                "Dalitz Plot analysis of the D⁺ → K⁻ K⁺ K⁺ decay",
            ),
            (
                "Observation of $B^0_{(s)} \\to J/\\psi p \\overline{p}$ decays and precision measurements of the $B^0_{(s)}$ masses",
                "Observation of B⁰_s → J/ψ pp decays and precision measurements of the B⁰_s masses",
            ),
            (
                "Measurement of $B^+$, $B^0$ and $\\Lambda_b^0$ production in $p\\mkern 1mu\\mathrm{Pb}$ collisions at $\\sqrt{s_{NN}} = 8.16 \\ \\rm TeV$",
                "Measurement of B⁺, B⁰ and Λ⁰_b production in p 1muPb collisions at √(s_NN) = 8.16 TeV",
            ),
            (
                "Measurement of the ratio of branching fractions of the decays $\\Lambda_b^0 \\!\\to \\psi(2S) \\Lambda$ and $\\Lambda_b^0 \\!\\to J\\!/\\!\\psi \\Lambda$",
                "Measurement of the ratio of branching fractions of the decays Λ⁰_b → ψ(2S) Λ and Λ⁰_b → J/ψΛ",
            ),
            (
                "Measurement of the mass and production rate of $\\Xi_b^-$ baryons",
                "Measurement of the mass and production rate of Ξ⁻_b baryons",
            ),
            (
                "Model-independent observation of exotic contributions to $B^0\\to J/\\psi K^+\\pi^-$ decays",
                "Model-independent observation of exotic contributions to B⁰ → J/ψ K⁺π⁻ decays",
            ),
            (
                "Measurement of the branching fraction and $C\\!P$ asymmetry in $B^{+}\\rightarrow J/\\psi \\rho^{+}$ decays",
                "Measurement of the branching fraction and CP asymmetry in B⁺ → J/ψρ⁺ decays",
            ),
            (
                "Search for the rare decay $B^{+} \\rightarrow \\mu^{+}\\mu^{-}\\mu^{+}\\nu_{\\mu}$",
                "Search for the rare decay B⁺ → μ⁺μ⁻μ⁺ν_μ",
            ),
            (
                "Study of the $B^0\\to \\rho(770)^0 K^*(892)^0$ decay with an amplitude analysis of $B^0\\to (\\pi^+\\pi^-) (K^+\\pi^-)$ decays",
                "Study of the B⁰ → ρ⁰(770) K*⁰(892) decay with an amplitude analysis of B⁰ → (π⁺π⁻) (K⁺π⁻) decays",
            ),
            (
                "Search for $CP$ violation through an amplitude analysis of $D^0\\rightarrow K^+ K^- \\pi^+ \\pi^-$ decays",
                "Search for CP violation through an amplitude analysis of D⁰ → K⁺ K⁻ π⁺ π⁻ decays",
            ),
            (
                "First measurement of charm production in fixed-target configuration at the LHC",
                "First measurement of charm production in fixed-target configuration at the LHC",
            ),
            (
                "Study of $\\Upsilon$ production in $p$Pb collisions at $\\sqrt{s_{NN}}=8.16$ TeV",
                "Study of Υ production in pPb collisions at √(s_NN) = 8.16 TeV",
            ),
            (
                "Measurement of the charm-mixing parameter $y_{CP}$",
                "Measurement of the charm-mixing parameter y_CP",
            ),
            (
                "Measurement of the branching fractions of the decays $D^+\\rightarrow K^-K^+K^+$, $D^+\\rightarrow \\pi^-\\pi^+K^+$ and $D^+_s\\rightarrow\\pi^-K^+K^+$",
                "Measurement of the branching fractions of the decays D⁺ → K⁻K⁺K⁺, D⁺ → π⁻π⁺K⁺ and D⁺_s → π⁻K⁺K⁺",
            ),
            (
                "Observation of two resonances in the $\\Lambda_b^0 \\pi^\\pm$ systems and precise measurement of $\\Sigma_b^\\pm$ and $\\Sigma_b^{*\\pm}$ properties",
                "Observation of two resonances in the Λ⁰_b π^± systems and precise measurement of Σ^±_b and Σ*^±_b properties",
            ),
            # LHCb lhcb_conf_feed
            (
                "Prospects for searches for long-lived particles after the LHCb detector upgrades",
                "Prospects for searches for long-lived particles after the LHCb detector upgrades",
            ),
            (
                "LHCb projections for proton-lead collisions during LHC Runs 3 and 4",
                "LHCb projections for proton-lead collisions during LHC Runs 3 and 4",
            ),
            (
                "Measurement of $B^+$, $B^0$ and $\\Lambda⁰_b$ production and nuclear modification in $p$Pb collisions at $\\sqrt{s_\\mathrm{NN}}=8.16 ~~\\text {TeV}$",
                "Measurement of B⁺, B⁰ and Λ⁰_b production and nuclear modification in pPb collisions at √(s_NN) = 8.16 TeV",
            ),
            (
                "Study of coherent $J/\\psi$ production in lead-lead collisions at $\\sqrt{s_{\\rm NN}} =5\\ \\rm{TeV}$ with the LHCb experiment",
                "Study of coherent J/ψ production in lead-lead collisions at √(s_NN) = 5 TeV with the LHCb experiment",
            ),
            (
                "Update of the LHCb combination of the CKM angle $\\gamma$",
                "Update of the LHCb combination of the CKM angle γ",
            ),
            (
                "Measurement of CP violation in the $B_s^0 \\to \\phi \\phi$ decay and search for the $B^0 \\to \\phi\\phi$ decay",
                "Measurement of CP violation in the B⁰_s → ϕϕ decay and search for the B⁰ → ϕϕ decay",
            ),
            (
                "Prompt $\\Lambda^+_{\\mathrm{c}}$ production in $p\\mathrm{Pb}$ collisions at $\\sqrt{s_{_{\\mathrm{NN}}}} = 5.02\\mathrm{\\,Te\\kern -0.1em V}$",
                "Prompt Λ⁺_c production in pPb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Update of the LHCb combination of the CKM angle $\\gamma$ using $B\\to DK$ decays",
                "Update of the LHCb combination of the CKM angle γ using B → DK decays",
            ),
            (
                "Measurement of antiproton production in $p$He collisions at $\\sqrt{s_{\\scriptscriptstyle\\rm NN}}=110$ GeV",
                "Measurement of antiproton production in pHe collisions at √(s_NN) = 110 GeV",
            ),
            (
                "Measurement of $J/\\psi$ and $D^0$ production in $p$Ar collisions at $\\sqrt{s_{NN}}=110$ GeV",
                "Measurement of J/ψ and D⁰ production in pAr collisions at √(s_NN) = 110 GeV",
            ),
            (
                "Measurement of time-dependent $C\\!P$-violating asymmetries in $B^0\\to\\pi^+\\pi^-$ and $B_s^0\\to K^+K^-$ decays at LHCb",
                "Measurement of time-dependent CP-violating asymmetries in B⁰ → π⁺π⁻ and B⁰_s → K⁺K⁻ decays at LHCb",
            ),
            (
                "First observation of a baryonic $B_s^0$ decay",
                "First observation of a baryonic B⁰_s decay",
            ),
            (
                "Measurement of $C\\!P$ asymmetry in $B_s^0\\to D_s^{\\mp}K^{\\pm}$ decays",
                "Measurement of CP asymmetry in B⁰_s → D_s^∓K^± decays",
            ),
            (
                "Study of the decay $B^{\\pm} \\to DK^{*\\pm}$ with two-body $D$ decays",
                "Study of the decay B^± → DK*^± with two-body D decays",
            ),
            (
                "Evidence for the rare decay $\\Sigma^+ \\to p \\mu^+ \\mu^-$",
                "Evidence for the rare decay Σ⁺ → p μ⁺ μ⁻",
            ),
            (
                "Updated limit for the decay $K_{\\rm\\scriptscriptstyle S}^0\\rightarrow\\mu^+\\mu^-$",
                "Updated limit for the decay K⁰_S → μ⁺μ⁻",
            ),
            (
                "Search for the rare decays $B^0_{(s)}\\to\\tau^+\\tau^-$",
                "Search for the rare decays B⁰_s → τ⁺τ⁻",
            ),
            (
                "$CP$-violating asymmetries from the decay-time distribution of prompt $D^0 \\to K^+ K^-$ and $D^0 \\to \\pi^+\\pi^-$ decays in the full $\\mbox{LHCb}$ Run 1 data sample. Measurement using unbinned, acceptance corrected decay-time.",
                "CP-violating asymmetries from the decay-time distribution of prompt D⁰ → K⁺ K⁻ and D⁰ → π⁺π⁻ decays in the full LHCb Run 1 data sample. Measurement using unbinned, acceptance corrected decay-time.",
            ),
            (
                "$CP$-violating asymmetries from the decay-time distribution of  prompt $D^0 \\to K^+K^-$  and  $D^0 \\to \\pi^+\\pi^-$ decays in the  full LHCb Run~1 data sample. Measurement using yield asymmetries in bins of decay time.",
                "CP-violating asymmetries from the decay-time distribution of prompt D⁰ → K⁺K⁻ and D⁰ → π⁺π⁻ decays in the full LHCb Run 1 data sample. Measurement using yield asymmetries in bins of decay time.",
            ),
            (
                "Dalitz plot analysis of the  $D^+ \\rightarrow K^- K^+ K^+$ decay with the isobar model",
                "Dalitz plot analysis of the D⁺ → K⁻ K⁺ K⁺ decay with the isobar model",
            ),
            (
                "Central exclusive production of $J/\\psi$ and $\\psi(2S)$ mesons in pp collisions at $\\sqrt{s}=13$ TeV",
                "Central exclusive production of J/ψ and ψ(2S) mesons in pp collisions at √(s) = 13 TeV",
            ),
            (
                "Search for $H^0 \\rightarrow b \\bar{b}$ or $c \\bar{c}$ in association with a $W$ or $Z$ boson in the forward region of $pp$ collisions",
                "Search for H⁰ → bb̅ or cc̅ in association with a W or Z boson in the forward region of pp collisions",
            ),
            (
                "LHCb dimuon and charm mass distributions",
                "LHCb dimuon and charm mass distributions",
            ),
            (
                "Search for structure in the $B_s^0\\pi^\\pm$ invariant mass spectrum",
                "Search for structure in the B⁰_s π^± invariant mass spectrum",
            ),
            (
                "Study of cold nuclear matter effects using prompt $D^0$ meson production in $p\\mathrm{Pb}$ collisions at LHCb",
                "Study of cold nuclear matter effects using prompt D⁰ meson production in pPb collisions at LHCb",
            ),
            # LHCb lhcb_paper_feed
            (
                "Search for $A' \\to \\mu^+ \\mu^-$ decays",
                "Search for A' → μ⁺ μ⁻ decays",
            ),
            (
                "Search for the doubly charmed baryon $\\Xi_{cc}^{+}$",
                "Search for the doubly charmed baryon Ξ⁺_cc",
            ),
            (
                "Amplitude analysis of the $B^+ \\to \\pi^+ \\pi^+ \\pi^-$ decay",
                "Amplitude analysis of the B⁺ → π⁺ π⁺ π⁻ decay",
            ),
            (
                "Observation of several sources of $CP$ violation in $B^+ \\to \\pi^+ \\pi^+ \\pi^-$ decays",
                "Observation of several sources of CP violation in B⁺ → π⁺ π⁺ π⁻ decays",
            ),
            (
                "Measurement of $\\psi(2S)$ production cross-sections in proton-proton collisions at $\\sqrt{s} = 7$ and 13 TeV",
                "Measurement of ψ(2S) production cross-sections in proton-proton collisions at √(s) = 7 and 13 TeV",
            ),
            (
                "Measurement of CP violation in the $B_s^0\\rightarrow\\phi\\phi$ decay and search for the $B^0\\rightarrow\\phi\\phi$ decay",
                "Measurement of CP violation in the B⁰_s → ϕϕ decay and search for the B⁰ → ϕϕ decay",
            ),
            (
                "Precision measurement of the $\\Lambda_c^+$, $\\Xi_c^+$ and $\\Xi_c^0$ baryon lifetimes",
                "Precision measurement of the Λ⁺_c, Ξ⁺_c and Ξ⁰_c baryon lifetimes",
            ),
            (
                "Observation of the $\\Lambda_b^0\\rightarrow \\chi_{c1}(3872)pK^-$ decay",
                "Observation of the Λ⁰_b → χ_c1(3872)pK⁻ decay",
            ),
            (
                "Updated measurement of time-dependent  CP-violating observables in $B^0_s \\to J/\\psi K^+K^-$ decays",
                "Updated measurement of time-dependent CP-violating observables in B⁰_s → J/ψ K⁺K⁻ decays",
            ),
            (
                "Measurement of $C\\!P$ observables in the process $B^0 \\to DK^{*0}$ with two- and four-body $D$ decays",
                "Measurement of CP observables in the process B⁰ → DK*⁰ with two- and four-body D decays",
            ),
            (
                "Amplitude analysis  of $B^\\pm \\to \\pi^\\pm K^+ K^-$ decays",
                "Amplitude analysis of B^± → π^± K⁺ K⁻ decays",
            ),
            (
                "Search for the lepton-flavour-violating decays $B^{0}_{s}\\to\\tau^{\\pm}\\mu^{\\mp}$ and $B^{0}\\to\\tau^{\\pm}\\mu^{\\mp}$",
                "Search for the lepton-flavour-violating decays B⁰_s → τ^±μ^∓ and B⁰ → τ^±μ^∓",
            ),
            (
                "Amplitude analysis of the $B^0_{(s)} \\to K^{*0} \\overline{K}^{*0}$ decays and measurement of the branching fraction of the $B^0 \\to K^{*0} \\overline{K}^{*0}$ decay",
                "Amplitude analysis of the B⁰_s → K*⁰K*⁰ decays and measurement of the branching fraction of the B⁰ → K*⁰K*⁰ decay",
            ),
            (
                "Measurement of $CP$-violating and mixing-induced observables in $B_s^0 \\to \\phi\\gamma$ decays",
                "Measurement of CP-violating and mixing-induced observables in B⁰_s → ϕγ decays",
            ),
            (
                "A search for $\\it{\\Xi}^{++}_{cc} \\rightarrow D^{+} p K^{-} \\pi^{+}$ decays",
                "A search for Ξ⁺⁺_cc → D⁺ p K⁻π⁺ decays",
            ),
            (
                "Measurement of charged hadron production in $Z$-tagged jets in proton-proton collisions at $\\sqrt{s}=8$ TeV",
                "Measurement of charged hadron production in Z-tagged jets in proton-proton collisions at √(s) = 8 TeV",
            ),
            (
                "Observation of a narrow pentaquark state, $P_c(4312)^+$, and of two-peak structure of the $P_c(4450)^+$",
                "Observation of a narrow pentaquark state, P⁺_c(4312), and of two-peak structure of the P⁺_c(4450)",
            ),
            (
                "Measurements of $CP$ asymmetries in charmless four-body $\\Lambda^0_b$ and $\\Xi_b^0$ decays",
                "Measurements of CP asymmetries in charmless four-body Λ⁰_b and Ξ⁰_b decays",
            ),
            (
                "Observation of an excited $B_c^+$ state",
                "Observation of an excited B⁺_c state",
            ),
            (
                "Near-threshold $D\\bar{D}$ spectroscopy and observation of a new charmonium state",
                "Near-threshold DD̅ spectroscopy and observation of a new charmonium state",
            ),
            (
                "Search for lepton-universality violation in $B^+\\to K^+\\ell^+\\ell^-$ decays",
                "Search for lepton-universality violation in B⁺ → K⁺ℓ⁺ℓ⁻ decays",
            ),
            (
                "Observation of $C\\!P$ violation in charm decays",
                "Observation of CP violation in charm decays",
            ),
            (
                "Measurement of the $CP$-violating phase $\\phi_s$ from $B_{s}^{0}\\to J/\\psi\\pi^+\\pi^-$ decays in 13 TeV $pp$ collisions",
                "Measurement of the CP-violating phase ϕ_s from B⁰_s → J/ψπ⁺π⁻ decays in 13 TeV pp collisions",
            ),
            (
                "Measurement of the mass difference between neutral charm-meson eigenstates",
                "Measurement of the mass difference between neutral charm-meson eigenstates",
            ),
            (
                "Search for $CP$ violation in $D^+_s\\to K_S^0\\pi^+$, $D^+\\to K_S^0K^+$ and $D^+\\to\\phi\\pi^+$ decays",
                "Search for CP violation in D⁺_s → K⁰_S π⁺, D⁺ → K⁰_S K⁺ and D⁺ → ϕπ⁺ decays",
            ),
            # LHCb lhcb_conf_feed
            (
                "Strong constraints on the $K^0_s \\to \\mu^+ \\mu^-$ branching fraction",
                "Strong constraints on the K⁰_s → μ⁺ μ⁻ branching fraction",
            ),
            (
                "Search for time-dependent $CP$ violation in $D^0 \\to K^+ K^-$ and $D^0 \\to \\pi^+ \\pi^-$ decays",
                "Search for time-dependent CP violation in D⁰ → K⁺ K⁻ and D⁰ → π⁺ π⁻ decays",
            ),
            (
                "Prospects for searches for long-lived particles after the LHCb detector upgrades",
                "Prospects for searches for long-lived particles after the LHCb detector upgrades",
            ),
            (
                "LHCb projections for proton-lead collisions during LHC Runs 3 and 4",
                "LHCb projections for proton-lead collisions during LHC Runs 3 and 4",
            ),
            (
                "Measurement of $B^+$, $B^0$ and $\\Lambda_b^0$ production and nuclear modification in $p$Pb collisions at $\\sqrt{s_\\mathrm{NN}}=8.16 ~~\\text {TeV}$",
                "Measurement of B⁺, B⁰ and Λ⁰_b production and nuclear modification in pPb collisions at √(s_NN) = 8.16 TeV",
            ),
            (
                "Study of coherent $J/\\psi$ production in lead-lead collisions at $\\sqrt{s_{\\rm NN}} =5\\ \\rm{TeV}$ with the LHCb experiment",
                "Study of coherent J/ψ production in lead-lead collisions at √(s_NN) = 5 TeV with the LHCb experiment",
            ),
            (
                "Update of the LHCb combination of the CKM angle $\\gamma$",
                "Update of the LHCb combination of the CKM angle γ",
            ),
            (
                "Measurement of CP violation in the $B_s^0 \\to \\phi \\phi$ decay and search for the $B^0 \\to \\phi\\phi$ decay",
                "Measurement of CP violation in the B⁰_s → ϕϕ decay and search for the B⁰ → ϕϕ decay",
            ),
            (
                "Prompt $\\Lambda^+_{\\mathrm{c}}$ production in $p\\mathrm{Pb}$ collisions at $\\sqrt{s_{_{\\mathrm{NN}}}} = 5.02\\mathrm{\\,Te\\kern -0.1em V}$",
                "Prompt Λ⁺_c production in pPb collisions at √(s_NN) = 5.02 TeV",
            ),
            (
                "Update of the LHCb combination of the CKM angle $\\gamma$ using $B\\to DK$ decays",
                "Update of the LHCb combination of the CKM angle γ using B → DK decays",
            ),
            (
                "Measurement of antiproton production in $p$He collisions at $\\sqrt{s_{\\scriptscriptstyle\\rm NN}}=110$ GeV",
                "Measurement of antiproton production in pHe collisions at √(s_NN) = 110 GeV",
            ),
            (
                "Measurement of $J/\\psi$ and $D^0$ production in $p$Ar collisions at $\\sqrt{s_{NN}}=110$ GeV",
                "Measurement of J/ψ and D⁰ production in pAr collisions at √(s_NN) = 110 GeV",
            ),
            (
                "Measurement of time-dependent $C\\!P$-violating asymmetries in $B^0\\to\\pi^+\\pi^-$ and $B_s^0\\to K^+K^-$ decays at LHCb",
                "Measurement of time-dependent CP-violating asymmetries in B⁰ → π⁺π⁻ and B⁰_s → K⁺K⁻ decays at LHCb",
            ),
            (
                "First observation of a baryonic $B_s^0$ decay",
                "First observation of a baryonic B⁰_s decay",
            ),
            (
                "Measurement of $C\\!P$ asymmetry in $B_s^0\\to D_s^{\\mp}K^{\\pm}$ decays",
                "Measurement of CP asymmetry in B⁰_s → D_s^∓K^± decays",
            ),
            (
                "Study of the decay $B^{\\pm} \\to DK^{*\\pm}$ with two-body $D$ decays",
                "Study of the decay B^± → DK*^± with two-body D decays",
            ),
            (
                "Evidence for the rare decay $\\Sigma^+ \\to p \\mu^+ \\mu^-$",
                "Evidence for the rare decay Σ⁺ → p μ⁺ μ⁻",
            ),
            (
                "Updated limit for the decay $K_{\\rm\\scriptscriptstyle S}^0\\rightarrow\\mu^+\\mu^-$",
                "Updated limit for the decay K⁰_S → μ⁺μ⁻",
            ),
            (
                "Search for the rare decays $B^0_{(s)}\\to\\tau^+\\tau^-$",
                "Search for the rare decays B⁰_s → τ⁺τ⁻",
            ),
            (
                "$CP$-violating asymmetries from the decay-time distribution of prompt $D^0 \\to K^+ K^-$ and $D^0 \\to \\pi^+\\pi^-$ decays in the full $\\mbox{LHCb}$ Run 1 data sample. Measurement using unbinned, acceptance corrected decay-time.",
                "CP-violating asymmetries from the decay-time distribution of prompt D⁰ → K⁺ K⁻ and D⁰ → π⁺π⁻ decays in the full LHCb Run 1 data sample. Measurement using unbinned, acceptance corrected decay-time.",
            ),
            (
                "$CP$-violating asymmetries from the decay-time distribution of  prompt $D^0 \\to K^+K^-$  and  $D^0 \\to \\pi^+\\pi^-$ decays in the  full LHCb Run~1 data sample. Measurement using yield asymmetries in bins of decay time.",
                "CP-violating asymmetries from the decay-time distribution of prompt D⁰ → K⁺K⁻ and D⁰ → π⁺π⁻ decays in the full LHCb Run 1 data sample. Measurement using yield asymmetries in bins of decay time.",
            ),
            (
                "Dalitz plot analysis of the  $D^+ \\rightarrow K^- K^+ K^+$ decay with the isobar model",
                "Dalitz plot analysis of the D⁺ → K⁻ K⁺ K⁺ decay with the isobar model",
            ),
            (
                "Central exclusive production of $J/\\psi$ and $\\psi(2S)$ mesons in pp collisions at $\\sqrt{s}=13$ TeV",
                "Central exclusive production of J/ψ and ψ(2S) mesons in pp collisions at √(s) = 13 TeV",
            ),
            (
                "Search for $H^0 \\rightarrow b \\bar{b}$ or $c \\bar{c}$ in association with a $W$ or $Z$ boson in the forward region of $pp$ collisions",
                "Search for H⁰ → bb̅ or cc̅ in association with a W or Z boson in the forward region of pp collisions",
            ),
        ],
    )
    def test_formatting(self, input_title, expected):
        """Test the list above."""
        new_title = cds_paper_bot.format_title(input_title)
        assert new_title == expected
