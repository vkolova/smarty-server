const axios = require('axios');



(async () => {
    
    const SERVER = 'http://localhost:8001';
    axios.defaults.headers.common.Authorization = 'Token 10200a9107a7fa87ae30eae506c6c728764f3b2f';

    try {
        const resp = await axios.post(`${SERVER}/api/accounts/register/`, {username: "vkolova"})
        console.log(resp.data)

    } catch (error) {
        console.log(error)
    }
})();