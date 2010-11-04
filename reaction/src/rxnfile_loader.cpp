/****************************************************************************
 * Copyright (C) 2009-2010 GGA Software Services LLC
 * 
 * This file is part of Indigo toolkit.
 * 
 * This file may be distributed and/or modified under the terms of the
 * GNU General Public License version 3 as published by the Free Software
 * Foundation and appearing in the file LICENSE.GPL included in the
 * packaging of this file.
 * 
 * This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
 * WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
 ***************************************************************************/


#include "reaction/reaction.h"
#include "reaction/query_reaction.h"
#include "reaction/reaction_highlighting.h"
#include "reaction/rxnfile_loader.h"
#include "molecule/molfile_loader.h"
#include "base_cpp/scanner.h"

RxnfileLoader::RxnfileLoader (Scanner& scanner): _scanner(scanner){
   highlighting = 0;
   _v3000 = false;
   ignore_stereocenter_errors = false;;
}

RxnfileLoader::~RxnfileLoader(){
}

void RxnfileLoader::loadReaction(Reaction &reaction){
   _rxn = &reaction;
   _brxn = &reaction;
   _qrxn = 0;
   _loadReaction();
}

void RxnfileLoader::loadQueryReaction(QueryReaction& rxn){
   _rxn = 0;
   _brxn = &rxn;
   _qrxn = &rxn;
   _loadReaction();
}


void RxnfileLoader::_loadReaction(){
   _brxn->clear();

   if (highlighting != 0)
      highlighting->clear();

   MolfileLoader molfileLoader(_scanner);

   molfileLoader.treat_x_as_pseudoatom = treat_x_as_pseudoatom;
   _readRxnHeader();

   _readReactantsHeader();
   for (int i = 0; i < _n_reactants; i++) {
      int index = _brxn->addReactant();
      if (highlighting != 0)
         highlighting->nondestructiveInit(*_brxn);

      _readMolHeader();
      _readMol(molfileLoader, index);
   }
   _readReactantsFooter();

   _readProductsHeader();
   for (int i = 0; i < _n_products; i++) {
      int index = _brxn->addProduct();

      if (highlighting != 0)
         highlighting->nondestructiveInit(*_brxn);
      _readMolHeader();
      _readMol(molfileLoader, index);
   }
   _readProductsFooter();

}

void RxnfileLoader::_readRxnHeader(){

   QS_DEF(Array<char>, header);

   _scanner.readString(header, true);

   if (strcmp(header.ptr(), "$RXN") == 0)
      _v3000 = false;
   else if (strcmp(header.ptr(), "$RXN V3000") == 0)
      _v3000 = true;
   else
      throw Error("bad header %s", header.ptr());

   _scanner.readString(_brxn->name, true);
   _scanner.skipString();
   _scanner.skipString();

   if (_v3000)
   {
      _scanner.skip(14); // "M  V30 COUNTS "
      _scanner.readString(header, true);
      if (sscanf(header.ptr(), "%d %d", &_n_reactants, &_n_products) < 2)
         throw Error("error reading counts: %s", header.ptr());
   }
   else
   {
      _n_reactants = _scanner.readIntFix(3);
      _n_products = _scanner.readIntFix(3);

      _scanner.skipString();
   }
}

void RxnfileLoader::_readProductsHeader(){
   if (!_v3000) {
      return;
   }

   QS_DEF(Array<char>, header);

   _scanner.readString(header, true);
   if (strcmp(header.ptr(), "M  V30 BEGIN PRODUCT") != 0){
      throw Error("bad products header: %s", header.ptr());
   }
}

void RxnfileLoader::_readReactantsHeader(){
   if (!_v3000) {
      return;
   }

   QS_DEF(Array<char>, header);

   _scanner.readString(header, true);
   if (strcmp(header.ptr(), "M  V30 BEGIN REACTANT") != 0){
      throw Error("bad reactants header: %s", header.ptr());
   }
}

void RxnfileLoader::_readMolHeader(){

   if (_v3000) {
      return;
   }
   QS_DEF(Array<char>, header);

   _scanner.readString(header, true);
   if (strcmp(header.ptr(), "$MOL") != 0)
      throw Error("bad molecule header: %s", header.ptr());
}

void RxnfileLoader::_readReactantsFooter(){
   if (!_v3000) {
      return;
   }
   QS_DEF(Array<char>, footer);

   _scanner.readString(footer, true);

   if (strcmp(footer.ptr(), "M  V30 END REACTANT") != 0)
      throw Error("bad reactants footer: %s", footer.ptr());
}

void RxnfileLoader::_readProductsFooter(){
   if (!_v3000) {
      return;
   }
   QS_DEF(Array<char>, footer);

   _scanner.readString(footer, true);

   if (strcmp(footer.ptr(), "M  V30 END PRODUCT") != 0)
      throw Error("bad products footer: %s", footer.ptr());
}


void RxnfileLoader::_readMol (MolfileLoader &loader, int index) {

   loader.reaction_atom_mapping = &_brxn->getAAMArray(index);
   loader.reaction_atom_inversion = &_brxn->getInversionArray(index);
   loader.reaction_bond_reacting_center = &_brxn->getReactingCenterArray(index);

   if (_qrxn != 0)
      loader.reaction_atom_exact_change = &_qrxn->getExactChangeArray(index);

   if (highlighting != 0)
      loader.highlighting = &highlighting->getGraphHighlighting(index);
   
   if (_qrxn != 0)
   {
      if (_v3000)
         loader.loadQueryCtab3000(_qrxn->getQueryMolecule(index));
      else
         loader.loadQueryMolecule(_qrxn->getQueryMolecule(index));
   }
   else
   {
      if (_v3000)
         loader.loadCtab3000(_rxn->getMolecule(index));
      else
         loader.loadMolecule(_rxn->getMolecule(index));
   }
}
