# -*- coding: utf-8 -*-

import sys
import numpy as np
import asyncio
sys.path.insert(0, "..")
import logging

from asyncua import Client, ua

class OPC:
    def __init__(self, url):
        self.client = None
        self.url = url
        self.is_connected = False

    async def connect_opc(self):
        try: 
            self.client = Client(self.url)
            await self.client.connect()
            print(f"Connexion OPC réussie")
            self.is_connected = True
            return True
        except Exception as e:
            print(f"Erreur de connexion OPC : {e}")
            self.is_connected = False
            return False

    # ----------------------------------------------------------
    #                     Methode WRITE TAG
    # ----------------------------------------------------------

    async def write_single_tag(self, tag, value, debug:bool=False):
        
        full_tag = "ns=3;s=" + tag
        tag_node = self.client.get_node(full_tag)
        try:
            data_type = await tag_node.read_data_type_as_variant_type()
            new_value = ua.DataValue(ua.Variant(value, data_type))
            await tag_node.write_value(new_value)
            if debug:
                print(f"Wrote {value} to tag: {tag}")
        except ua.uaerrors._auto.BadTypeMismatch as e:
            print(f"Failed to write to tag. Type mismatch. Error: {e}")
        except ua.uaerrors._auto.BadOutOfRange as e:
            print(f"Failed to write to tag. Value out of range. Error: {e}")
        except Exception as e:
            print(f"Failed to write to tag. Unknown error: {e}")
            
    async def OPC_Write(self, tags:list[str], values:list[str], debugVal:bool=False):
        '''
        tags : Tableau d'adresses de tags.
        values : Tableau de valeurs associées aux adresses de tags.
        '''
        for tag, value in zip(tags, values):
            await self.write_single_tag(tag, value, debugVal)
            


    # ----------------------------------------------------------
    #                     Methode READ TAG
    # ----------------------------------------------------------

    async def read_single_tag(self, tag, debug:bool=False):

        full_tag = "ns=3;s=" + tag
        tag_node = self.client.get_node(full_tag)
        value = await tag_node.read_value()
        data_type = await tag_node.read_data_type_as_variant_type()
        if debug:
            print(f"{tag} - Value: {value}, Type: {data_type}")
        return {"value": value, "type": data_type}
            
    async def OPC_Read(self, tags:list[str], debugVal:bool=False):
        '''
        tags : Tableau d'adresses de tags.
        '''
        data = {}
        for tag in tags:
            result = await self.read_single_tag(tag, debugVal)
            data[tags.index(tag)] = result['value']
        return data

async def main():
    url = 'opc.tcp://172.29.0.21:4840'
    testop = OPC(url)
    await testop.Connect_Opc()
    #choix_of = await testop.read_single_tag("Choix_OF")
    #choix_of = await testop.OPC_Read(["Choix_OF"])
    #print(choix_of)
    #await testop.write_single_tag("Production_faite", 0)
    


if __name__ == '__main__':
    asyncio.run(main())
    