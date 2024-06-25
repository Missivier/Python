import xmlrpc.client
import asyncio

class ERP: 
    def __init__(self, url_erp, db, username, password):
        self.url_erp = url_erp
        self.db = db
        self.username = username
        self.password = password
        self.common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url_erp))
        self.uid = self.common.authenticate(db, username, password, {})
        self.models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url_erp))
        self.qty_producing = "0"
        
    def authenticate(self):
        try:
            if self.uid:
                print('Connexion ERP réussie. UID:', self.uid)
            else: 
                print('Echec de connexion ERP')

        except Exception as e:
            print('Erreur de connexion ERP:', e)

    async def get_of(self, afficher:bool=False):

        if self.uid:
            # Recherche d'ordres de fabrication en excluant certains états
            orders_ids = self.models.execute_kw(
                self.db, self.uid, self.password,
                'mrp.production', 'search',
                [[['state', 'not in', ['done', 'cancel', 'to_close']]]]
            )

            # Lecture des détails des ordres de fabrication filtrés
            self.orders = self.models.execute_kw(
                self.db, self.uid, self.password,
                'mrp.production', 'read', [orders_ids],
                {'fields': ['name', 'product_id','date_planned_start', 'product_qty', 'qty_producing', 'create_date']}
            )
            if afficher:
                print("\nOrdres de fabrication en cours:")
                for order in self.orders:
                    print(f"\n\tDate de création : {order['create_date']}")
                    print(f"\t- {order['name']} -\n\t  Recette: {order['product_id']},\n\t  Date planned start: {order['date_planned_start']},\n\t  Quantity: {order['product_qty']},\n\t  Qty producing: {order['qty_producing']}")
                    print("\t----" + "-"*len(order['name']))
                    # Réinitialisation des listes pour éviter l'accumulation de données
                    self.ordres_fabrication = []
                    self.recette = []
                    self.dates_ordres_fabrication = []
                    self.quantite_a_produire = []
                    self.qty_producing = []
                    self.date_creation = []

                for order in self.orders:
                    self.ordres_fabrication.append(order['name'])
                    self.recette.append(order['product_id'])
                    self.dates_ordres_fabrication.append(order['date_planned_start'])
                    self.quantite_a_produire.append(order['product_qty'])
                    self.qty_producing.append(order['qty_producing'])
                    self.date_creation.append(order['create_date'])
        else:
            print('Échec de la connexion à Odoo.')

    async def choice_of(self, choix:bool=True):
        if choix:
            # Tri des OFs par date de production la plus proche
            self.orders.sort(key=lambda x: x["date_planned_start"])
            print(f"\nOF le plus proche : {self.orders[0]['id']}")
            datas = []
            for item in self.orders[0]:
                if type(self.orders[0][item]) == type(float()):
                    self.orders[0][item] = int(self.orders[0][item])
                datas.append(self.orders[0][item])
            datas[2] = datas[2][0]
            print(datas[6])
            del datas[0]
            return datas #qty_producing
        
        elif not choix:
            # Tri des OFs par date de création le plus anciens
            self.orders.sort(key=lambda x: x['create_date'])
            print(f"\nOF le plus ancien : {self.orders[0]['id']}")
            datas = []
            for item in self.orders[0]:
                if type(self.orders[0][item]) == type(float()):
                    self.orders[0][item] = int(self.orders[0][item])
                datas.append(self.orders[0][item])
            datas[2] = datas[2][0]
            del datas[0]
            return datas
        
        else:
            print("Erreur de choix")
            
    def change_in_progress(self, OF_select):
        if self.uid:
            ID_select = self.models.execute_kw(
                self.db, self.uid, self.password,
                'mrp.production', 'search',
                [[['name', '=', OF_select], 
                ['state', 'not in', ['done', 'cancel', 'close']]]]
            )
        if ID_select:
            # Mise à jour de l'état de l'OF en cours de production
            self.models.execute_kw(
                self.db, self.uid, self.password, 'mrp.production', 'write', [ID_select, {'state': 'progress'}]
            )
    
    def get_of_state(self, selected_of):
        if self.uid:
            ID_select = self.models.execute_kw(
                self.db, self.uid, self.password,
                'mrp.production', 'search',
                [[['name', '=', selected_of]]]
            )
            if ID_select:
                of_state = self.models.execute_kw(
                    self.db, self.uid, self.password,
                    'mrp.production', 'read', [ID_select[0]], {'fields': ['state']}
                )
                return of_state[0]['state']
            else:
                return "OF not found"
        else:
            return "Not connected to ERP"
    
    def write_qty_producing(self, OF_select, new_qty_producing):
        if self.uid:
            ID_select = self.models.execute_kw(
                self.db, self.uid, self.password,
                'mrp.production', 'search',
                [[['name', '=', OF_select], 
                ['state', 'not in', ['done', 'cancel', 'close']]]]
            )
            
        if ID_select:
            self.models.execute_kw(
                self.db, self.uid, self.password, 'mrp.production', 'write',
                [ID_select, {'qty_producing': new_qty_producing}]
            )
            print(ID_select)
            print(f"Quantité produite mise à jour avec succès pour le produit")

    def deconnexion(self):
        if self.uid:

            self.uid = 0
            print('\nDéconnexion réussie.')
        else:
            print('Aucun utilisateur connecté.')


if __name__ == '__main__':

    url_erp = 'http://172.18.0.1:8007'

    db = 'Groupe7'

    username = 'Admin'

    password = 'Admin'

    test = ERP(url_erp, db, username, password)
    test.authenticate()
    asyncio.run(test.get_of())
    of_to_produce = asyncio.run(test.choice_of())
    print(of_to_produce)
    test.deconnexion()
