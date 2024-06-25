from odoo import ERP    
from opc import OPC
import asyncio

class application:
    def __init__(self, erp_url, erp_db, erp_username, erp_password, opc_ua_server_assemblage_url, opc_ua_server_condi_url,  debug:bool=False):
        self.erp = ERP(erp_url, erp_db, erp_username, erp_password)
        self.opc_A = OPC(opc_ua_server_assemblage_url)
        self.opc_C = OPC(opc_ua_server_condi_url)
        self.previous_state = None
        self.actual_state = False
        self.debugMode = debug
        self.refresh = None


    async def gestion_ihm(self, cellule:str=None):
        opc_name = f"opc_{cellule}"
        self.opc_obj = getattr(self, opc_name)
        
        self.actual_state = choix[0] # Affectation de l'état actuel avec le choix de l'OF 
        self.tag_prod_distante = f"{cellule}_OPCUA_Prod_distante"
        self.Choix_OF = f"{cellule}_OPCUA_Choix_OF"
        self.quantite_produite = f"{cellule}_OPCUA_Quantite_produite"
        self.DCY == None
        # variable de l'état de l'OF sélectionner      
        self.etat_en_cours = self.erp.get_of_state(self.OF_prodValues[0])
        self.etat_to_close = 'to_close'
        self.mode_distant_[cellule] = await self.opc_obj.OPC_Read([self.tag_prod_distante]) # Affectation variable pour production distante activée
        choix = await self.opc_obj.OPC_Read([self.Choix_OF]) # Affectation variable pour le choix de l'OF 
                
        # COnnection OPC 
        if not self.opc_obj.is_connected:
            await self.opc_obj.connect_opc()
            
        # Sélection de l'OF à affiché si click sur bouton choix de l'OF 
        if (self.actual_state != self.previous_state and self.mode_distant[0] == False) or self.refresh == True:
                #Initialisation de la variable refresh
                self.refresh = False
                # Récupération des OFs dans l'ERP   
                await self.erp.get_of(self.debugMode)
                self.OF_prod = [str()] * 6
                self.OF_prodValues = [str()] * 6
                self.OF_prod = ["{cellule}_OPCUA_Numero_OF", "{cellule}_OPCUA_Recette""{cellule}_OPCUA_Recette", "{cellule}_OPCUA_Date_limite", "{cellule}_OPCUA_Quantite_a_produire", "{cellule}_OPCUA_Quantite_produite", "{cellule}_OPCUA_Date_creation"]
                self.OF_prodValues = await self.erp.choice_of(choix[0])
                
                await self.opc_assemblage.OPC_Write(self.OF_prod ,self.OF_prodValues, self.debugMode)
                self.previous_state = choix[0]
                self.message = True
        else: 
            if self.message:
                print(f"Attente de changement de la variable Choix_OF_{cellule}: {choix[0]}")
                self.message = False 
                        
                        
        if self.message_prod:
            print(f"Attente de la variable Prod Distante: {self.mode_distant[0]}")
            self.message_prod = False
        
        # Passage l'OF à l'état en cours         
        if self.mode_distant[0] == True :
            self.erp.change_in_progress(self.OF_prodValues[0])
            print(self.OF_prodValues[4])
            new_quantite_produite = await self.opc_obj.OPC_Read([self.quantite_produite ])
            self.erp.write_qty_producing(self.OF_prodValues[0], new_quantite_produite[0])        
            
        # Condition si l'OF est terminé
        if self.etat_en_cours == self.etat_to_close:
            self.refresh = True
        
    async def stop_RAZ_OF(self, cellule:str=None):
        self.BP_RAZ = f"{cellule}_OPCUA_Stop_RAZ_OF"
        self.stop_RAZ_OF = await self.opc_obj.OPC_Read([self.BP_RAZ])
        if self.stop_RAZ_OF:
            # Remise de la quantité produite à zéro 
            self.erp.write_qty_producing(self.OF_prodValues[0], 0) 
            # Arrêter l'autorisation production à distance
            self.aut_ok = False
    
    
    async def fin_prod_distant(self, cellule:str=None):
        self.Fin_Prod = ["A_OPCUA_Autorisation_Prod", "C_OPCUA_Autorisation_Prod"]
        self.Fin_OF = f"{cellule}_OPCUA_Fin_OF"
        self.etat_Fin_OF = await self.opc_obj.OPC_Read([self.Fin_OF])
        if self.etat_Fin_OF and self.etat_en_cours == self.etat_to_close: 
            await self.opc_A.OPC_Write(self.Fin_Prod[0] , True, self.debugMode)
            await self.opc_C.OPC_Write(self.Fin_Prod[1] , True, self.debugMode)

    async def run(self):
        # Authentification à l'ERP
        self.erp.authenticate()
        self.aut_ok = None
        self.message_prod = True
        self.message = None
        while True:
            try:
                await self.gestion_ihm("A") # A == Cellule Assemblage
                await self.gestion_ihm("C") # C == Cellule Conditionnement
                self.DCY_Assemblage = await self.opc_A.OPC_Read("A_OPCUA_DCY")
                self.DCY_Condi = await self.opc_C.OPC_Read("C_OPCUA_DCY")
                if self.mode_distant_A and self.mode_distant_B and self.DCY_Assemblage and self.DCY_Condi:
                    self.autorisation = ["A_OPCUA_Autorisation_Prod", "C_OPCUA_Autorisation_Prod"]
                    self.aut_ok = [True]
                    await self.opc_A.OPC_Write(self.autorisation[0] ,self.aut_ok[0], self.debugMode)
                    await self.opc_C.OPC_Write(self.autorisation[1] ,self.aut_ok[0], self.debugMode)
                else :
                    self.autorisation = ["A_OPCUA_Autorisation_Prod", "C_OPCUA_Autorisation_Prod"]
                    self.aut_ok = [False]
                    await self.opc_A.OPC_Write(self.autorisation[0] ,self.aut_ok[0], self.debugMode)
                    await self.opc_C.OPC_Write(self.autorisation[1] ,self.aut_ok[0], self.debugMode)
                
                await self.fin_prod_distant("A")
                await self.fin_prod_distant("C")
                await self.stop_RAZ_OF("A")
                await self.stop_RAZ_OF("C")
                
            except Exception as e:
                print(f"Erreur : {e}")
            finally:
                await asyncio.sleep(0.5) # Tempo entre chaque boucle
                

if __name__ == '__main__':
    erp_url = 'http://172.17.0.1:8007'#
    erp_db = 'Groupe7'
    erp_username = 'Admin'
    erp_password = 'Admin'
    #opc_url_ass = "opc.tcp://172.29.0.21:4840" #URL Prod 
    opc_url_ass = "opc.tcp://192.168.201.84:4840" #URL test 
    opc_url_condi = 'opc.tcp://localhost:4841'

    app = application(erp_url, erp_db, erp_username, erp_password, opc_url_ass, opc_url_condi, debug=False)

    asyncio.run(app.run())
    
