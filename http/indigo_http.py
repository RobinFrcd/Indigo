import asyncio
from enum import Enum
from typing import Dict, List, Optional, Union, Tuple, Generator

from fastapi import FastAPI, Response, Request
from indigo import IndigoException, IndigoObject
from pydantic import BaseModel
from indigo_tools import indigo, indigo_new

app = FastAPI()

base_url_indigo = "/indigo"
base_url_indigo_object = "/indigoObject"
resp_header_cont_type = "application/vnd.api+json"


class SupportedTypes(Enum):
    MOLFILE = "molfile"
    SMILES = "smiles"
    BOOL = "bool"
    INT = "int"
    REACTION = "reaction"
    GROSSFORMULA = "grossformula"
    FLOAT = "float"


class AttributesModel(BaseModel):
    content: str


class DataModel(BaseModel):
    type: SupportedTypes = None
    attributes: List[AttributesModel] = None


class IndigoRequest(BaseModel):
    data: DataModel = None


class IndigoResponse(BaseModel):
    data: Optional[Dict] = None
    meta: Optional[Dict] = None
    errors: Optional[List[str]] = None


def get_indigo_object(request: IndigoRequest) -> Generator[IndigoObject, None, None]:
    """extract molecules from request"""
    if isinstance(request.data.attributes, list):
        item: AttributesModel
        type_ = request.data.type
        for attribute in request.data.attributes:
            if type_ == SupportedTypes.SMILES:
                yield indigo().loadMolecule(attribute.content)
            elif type_ == SupportedTypes.MOLFILE:
                yield indigo().loadMoleculeFromBuffer(bytes(attribute.content, "utf-8"))
            elif type_ == SupportedTypes.REACTION:
                yield indigo().loadReaction(attribute.content)
            else:
                raise AttributeError(f"Unsupported type {type_}")
    else:
        raise AttributeError(f"Unsupported attributes {type(request.data.attributes)}")


def apply(molecule: IndigoObject, function: str) -> IndigoResponse:
    """apply function to molecule and form IndigoResponse"""
    indigo_response = IndigoResponse()
    try:
        getattr(molecule, function)()
        indigo_response.data = {
            "type": SupportedTypes.MOLFILE,
            "attributes": {"content": molecule.molfile()},
        }
    except IndigoException as err_:
        indigo_response.errors = [
            str(err_),
        ]
    return indigo_response


def apply_bool(molecule: IndigoObject, function: str) -> IndigoResponse:
    """apply boolean function to molecule and form bool IndigoResponse"""
    indigo_response = IndigoResponse()
    try:
        result: bool = getattr(molecule, function)()
        indigo_response.data = {
            "type": SupportedTypes.BOOL,
            "attributes": {"content": bool(result)},
        }
    except IndigoException as err_:
        indigo_response.errors = [str(err_)]
    return indigo_response


def apply_int(molecule: IndigoObject, function: str) -> IndigoResponse:
    indigo_response = IndigoResponse()
    try:
        result: int = getattr(molecule, function)()
        indigo_response.data = {
            "type": SupportedTypes.INT,
            "attributes": {"content": int(result)},
        }
    except IndigoException as err_:
        indigo_response.errors = [str(err_)]
    return indigo_response


def apply_float(molecule: IndigoObject, function: str) -> IndigoResponse:
    indigo_response = IndigoResponse()
    try:
        result: float = getattr(molecule, function)()
        indigo_response.data = {
            "type": SupportedTypes.FLOAT,
            "attributes": {"content": float(result)},
        }
    except IndigoException as err_:
        indigo_response.errors = [str(err_)]
    return indigo_response


@app.middleware("http")
async def isolate_indigo_session(request: Request, call_next):
    with indigo_new():
        response = await call_next(request)
        if not request.scope["path"].startswith("/docs"):
            response.headers["Content-Type"] = resp_header_cont_type
        return response


@app.post(f"{base_url_indigo}/checkStructure")
async def check_structure(body: IndigoRequest):
    # todo: find documentation about this function
    pass


@app.post(f"{base_url_indigo}/commonBits", response_model=IndigoResponse)
async def common_bits(indigo_request: IndigoRequest) -> IndigoResponse:
    indigo_response = IndigoResponse()
    try:
        mol1, mol2 = list(get_indigo_object(indigo_request))
        indigo_response.data = {
            "type": "common_bits",
            "attributes": {
                "common_bits": indigo().commonBits(
                    mol1.fingerprint("sim"), mol2.fingerprint("sim")
                )
            },
        }
    except IndigoException as err_:
        indigo_response.errors = [
            str(err_),
        ]

    return indigo_response


async def decompose_molecules(scaffold: str, structures: str) -> str:
    # todo: find documentation about this function
    pass


@app.post(f"{base_url_indigo}/exactMatch", response_model=IndigoResponse)
async def exact_match(indigo_request: IndigoRequest) -> IndigoResponse:
    indigo_response = IndigoResponse()
    try:
        mol1, mol2 = list(get_indigo_object(indigo_request))
        match = True if indigo().exactMatch(mol1, mol2) else False
        indigo_response.data = {
            "type": "bool",
            "attributes": {"is_match": match},
        }

    except IndigoException as err_:
        indigo_response.errors = [
            str(err_),
        ]

    return indigo_response


@app.get(f"{base_url_indigo}/version", response_model=IndigoResponse)
async def indigo_version() -> IndigoResponse:
    indigo_response = IndigoResponse()
    mol1 = indigo().loadMolecule("CN1C=NC2=C1C(=O)N(C(=O)N2C)C")
    indigo_response.data = {
        "type": "version_string",
        "attributes": {"content": indigo().version()},
    }
    return indigo_response


@app.post(f"{base_url_indigo_object}/aromatize", response_model=IndigoResponse)
async def aromatize(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule_string = indigo_request.data.attributes[0].content
    molecule = indigo().loadMolecule(molecule_string)
    return apply(molecule, "aromatize")


@app.post(f"{base_url_indigo_object}/smiles")
async def smiles(indigo_request: IndigoRequest) -> IndigoResponse:
    indigo_response = IndigoResponse()
    molecule1 = indigo_request.data.attributes[0].content
    try:
        mol1 = indigo().loadMolecule(molecule1)
        indigo_response.data = {
            "type": "smiles",
            "attributes": {"content": mol1.smiles()},
        }
    except IndigoException as err_:
        indigo_response.errors = [
            str(err_),
        ]
    return indigo_response


@app.post(f"{base_url_indigo_object}/smarts")
async def smarts(indigo_request: IndigoRequest) -> IndigoResponse:
    # TODO: query molecule only
    indigo_response = IndigoResponse()
    molecule1 = indigo_request.data.attributes.arg1.content
    try:
        mol1 = indigo().loadMolecule(molecule1)
        indigo_response.data = {
            "type": "smarts",
            "attributes": {"content": mol1.smarts()},
        }
    except IndigoException as err_:
        indigo_response.errors = [
            str(err_),
        ]
    return indigo_response


@app.post(f"{base_url_indigo_object}/standardize")
async def standardize(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply(molecule, "standardize")


@app.post(f"{base_url_indigo_object}/unfoldHydrogens")
async def unfold_hydrogens(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply(molecule, "unfoldHydrogens")


@app.post(f"{base_url_indigo_object}/validateChirality")
async def validate_chirality(indigo_request: IndigoRequest) -> IndigoResponse:
    indigo_response = IndigoResponse()
    molecule, *_ = list(get_indigo_object(indigo_request))
    molecule.validateChirality()
    return indigo_response


@app.post(f"{base_url_indigo_object}/check3DStereo")
async def check_3d_stereo(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_bool(molecule, "check3DStereo")


@app.post(f"{base_url_indigo_object}/checkAmbiguousH")
async def check_ambiguous_h(indigo_request: IndigoRequest) -> IndigoResponse:
    # TODO: Accepts a molecule or reaction (but not query molecule or query reaction).
    # Returns a string describing the first encountered mistake with ambiguous H counter.
    # Returns an empty string if the input molecule/reaction is fine.
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_bool(molecule, "checkAmbiguousH")


@app.post(f"{base_url_indigo_object}/checkBadValence")
async def check_bad_valence(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_bool(molecule, "checkBadValence")


@app.post(f"{base_url_indigo_object}/checkChirality")
async def check_chirality(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_bool(molecule, "checkChirality")


@app.post(f"{base_url_indigo_object}/checkQuery")
async def check_query(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_bool(molecule, "checkQuery")


@app.post(f"{base_url_indigo_object}/checkRGroups")
async def check_rgroups(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_bool(molecule, "checkRGroups")


@app.post(f"{base_url_indigo_object}/checkStereo")
async def check_stereo(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_bool(molecule, "checkStereo")


@app.post(f"{base_url_indigo_object}/checkValence")
async def check_valence(indigo_request: IndigoRequest) -> IndigoResponse:
    # TODO: iterate all atoms
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_bool(molecule, "checkValence")


@app.post(f"{base_url_indigo_object}/clean2d")
async def clean_2d(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply(molecule, "clean2d")


@app.post(f"{base_url_indigo_object}/clear")
async def clear(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply(molecule, "clear")


@app.post(f"{base_url_indigo_object}/clearAAM")
async def clear_aam(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply(molecule, "clearAAM")


@app.post(f"{base_url_indigo_object}/clearAlleneCenters")
async def clear_allene_centers(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply(molecule, "clearAlleneCenters")


@app.post(f"{base_url_indigo_object}/clearAttachmentPoints")
async def clear_attachment_points(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply(molecule, "clearAttachmentPoints")


@app.post(f"{base_url_indigo_object}/clearCisTrans")
async def clear_cis_trans(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply(molecule, "clearCisTrans")


@app.post(f"{base_url_indigo_object}/clearStereocenters")
async def clear_stereocenters(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply(molecule, "clearStereocenters")


@app.post(f"{base_url_indigo_object}/countAlleneCenters")
async def count_allene_centers(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_int(molecule, "countAlleneCenters")


@app.post(f"{base_url_indigo_object}/countAtoms")
async def count_atoms(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_int(molecule, "countAtoms")


@app.post(f"{base_url_indigo_object}/countAttachmentPoints")
async def count_attachment_points(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_int(molecule, "countAttachmentPoints")


@app.post(f"{base_url_indigo_object}/countBonds")
async def count_attachment_points(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_int(molecule, "countAttachmentPoints")


@app.post(f"{base_url_indigo_object}/countCatalysts")
async def count_catalysts(indigo_request: IndigoRequest) -> IndigoResponse:
    reaction, *_ = list(get_indigo_object(indigo_request))
    return apply_int(reaction, "countCatalysts")


@app.post(f"{base_url_indigo_object}/countComponents")
async def count_components(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_int(molecule, "countComponents")


@app.post(f"{base_url_indigo_object}/countDataSGroups")
async def count_data_sgroups(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_int(molecule, "countDataSGroups")


@app.post(f"{base_url_indigo_object}/countGenericSGroups")
async def count_generic_sgroups(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_int(molecule, "countGenericSGroups")


@app.post(f"{base_url_indigo_object}/countHeavyAtoms")
async def count_heavy_atoms(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_int(molecule, "countHeavyAtoms")


@app.post(f"{base_url_indigo_object}/countHydrogens")
async def count_hydrogens(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_int(molecule, "countHydrogens")


@app.post(f"{base_url_indigo_object}/countImplicitHydrogens")
async def count_implicit_hydrogens(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_int(molecule, "countImplicitHydrogens")


@app.post(f"{base_url_indigo_object}/countMolecules")
async def count_molecules(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_int(molecule, "countMolecules")


@app.post(f"{base_url_indigo_object}/countMultipleGroups")
async def count_multiple_groups(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_int(molecule, "countMultipleGroups")


@app.post(f"{base_url_indigo_object}/countProducts")
async def count_products(indigo_request: IndigoRequest) -> IndigoResponse:
    reaction, *_ = list(get_indigo_object(indigo_request))
    return apply_int(reaction, "countProducts")


@app.post(f"{base_url_indigo_object}/countPseudoatoms")
async def count_pseudoatoms(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_int(molecule, "countPseudoatoms")


@app.post(f"{base_url_indigo_object}/countRGroups")
async def count_rgroups(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_int(molecule, "countRGroups")


@app.post(f"{base_url_indigo_object}/countRSites")
async def count_rsites(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_int(molecule, "countRSites")


@app.post(f"{base_url_indigo_object}/countReactants")
async def count_reactants(indigo_request: IndigoRequest) -> IndigoResponse:
    reaction, *_ = list(get_indigo_object(indigo_request))
    return apply_int(reaction, "countReactants")


@app.post(f"{base_url_indigo_object}/countRepeatingUnits")
async def count_repeating_units(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_int(molecule, "countRepeatingUnits")


@app.post(f"{base_url_indigo_object}/countSSSR")
async def count_sssr(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_int(molecule, "countSSSR")


@app.post(f"{base_url_indigo_object}/countStereocenters")
async def count_stereo_centers(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_int(molecule, "countStereocenters")


@app.post(f"{base_url_indigo_object}/countSuperatoms")
async def count_superatoms(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_int(molecule, "countSuperatoms")


@app.post(f"{base_url_indigo_object}/dearomatize")
async def clear_dearomatize(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply(molecule, "dearomatize")


@app.post(f"{base_url_indigo_object}/grossFormula")
async def gross_formula(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return IndigoResponse(
        data={
            "type": SupportedTypes.GROSSFORMULA,
            "attributes": {"content": molecule.grossFormula()},
        }
    )


@app.post(f"{base_url_indigo_object}/hasCoord")
async def has_coord(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_bool(molecule, "hasCoord")


@app.post(f"{base_url_indigo_object}/isChiral")
async def is_chiral(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_bool(molecule, "isChiral")


@app.post(f"{base_url_indigo_object}/molecularWeight")
async def molecular_weight(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply_float(molecule, "molecularWeight")


@app.post(f"{base_url_indigo_object}/normalize")
async def normalize(indigo_request: IndigoRequest) -> IndigoResponse:
    molecule, *_ = list(get_indigo_object(indigo_request))
    return apply(molecule, "normalize")
