const assert = require('assert');
let Migrations = artifacts.require('./Migrations.sol');
let TestToken = artifacts.require('./TestToken.sol');

module.exports = (deployer, network, accounts) => {
    deployer.deploy(Migrations);
    deployer.deploy(TestToken).then(async() => {
        instance = await TestToken.deployed()
        console.log(`TestToken contract deployed at ${instance.address}`);

        // give tokens to the testing account
        let numTokens = 1000;
        ok = await instance.assign(accounts[0], web3.toWei(numTokens, "ether"));
        assert.ok(ok);

        // check resulting balance
        let balanceWei = (await instance.balanceOf(accounts[0])).toNumber();
        assert.equal(web3.fromWei(balanceWei, "ether"), numTokens);
        console.log(`Assigned ${numTokens} tokens to account ${accounts[0]} ...`);
    });
};
