import express from 'express';
const router=express.Router();
import {Configuration, PlaidApi, PlaidEnvironments, Products, CountryCode} from 'plaid';

const config=new Configuration({
    basePath: PlaidEnvironments.sandbox,
    baseOptions:{
        headers:{
            'PLAID-CLIENT-ID': process.env.PLAID_CLIENT_ID,
            'PLAID-SECRET': process.env.PLAID_SECRET
        },
    },
});

//frontend to open plaid link UI
const plaidClient=new PlaidApi(config);
router.post('/create-link-token', async (req, res)=>{
    try{
        const response=await plaidClient.linkTokenCreate({
            user:{
                client_user_id: 'user-id-123' //or use req.user.id.toString()
            },
            client_name:'Plaid Test App',
            products:[Products.Transactions],
            country_codes:[CountryCode.Us],
            language:'en',
        });
        res.json({link_token: response.data.link_token});
    }
    catch(err){
        res.status(500).json({error: err.message});
    }
});

//once user connects bank, exchange public token for access
router.post('/exchange-public-token', async(req, res)=>{
    try{
        const {public_token}=req.body;
        const response=await plaidClient.itemPublicTokenExchange({public_token});
        res.json({access_token:response.data.access_token}); //but here it should be stored in DB
    }
    catch(err){
        res.status(500).json({error: err.message});
    }
});

//get acc+balance, access_token shhould be taken from DB, may be getAccessTokenDB(req.user.id)
router.post('/accounts', async(req, res)=>{
    try{
        const {access_token}=req.body;
        const response=await plaidClient.accountsGet({access_token});
        res.json(response.data.accounts);
    }
    catch(err){
        res.status(500).json({error: err.message});
    }
});

//get transactions for last 30 days
router.post('/transactions', async(req, res)=>{
    try{
        const {access_token}=req.body;
        const today = new Date().toISOString().split('T')[0];
        const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
        .toISOString().split('T')[0];

        //can use transactionsSync and drop the dates
        const response = await plaidClient.transactionsGet({
        access_token,
        start_date: thirtyDaysAgo,
        end_date: today,
        });
        res.json(response.data.transactions);
    }
    catch(err){
        res.status(500).json({error: err.message});
    }
});

//get transactions real time using transactionSync
/* router.post('/transactions', async(req,res)=>{
    try{
        const {access_token, cursor}=req.body;
        const response=await plaidClient.transactionsSync({
            access_token,
            curson: cursor || null,
        });
        res.json({
            transactions:response.data.added,
            modified:response.data.modified,
            removed:response.data.removed,
            has_more:response.data.has_more,
            next_cursor:response.data.next_cursor
        });
    }
    catch(err){
        res.status(500).json({error:err.message});
    }
}); */

export default router;