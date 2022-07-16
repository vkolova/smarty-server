### POST /api/accounts/register/
Приема

```
{
    username: "vkolova",
    password: "..."
}
```

връща
```json
{
  user: {
    id: 1,
    username: 'vkolova',
    score: 0,
    avatar: 'http://prikachi.com/images/569/9566569j.png',
    level: 1,
    games: 0,
    wins: 0,
    streak: 0,
    rang_position: 1
  },
  token: '10200a9107a7fa87ae30eae506c6c728764f3b2f'
}
```

### POST /api/accounts/login/
Приема

```
{
    username: "vkolova",
    password: "..."
}
```

връща
```json
{
  user: {
    id: 1,
    username: 'vkolova',
    score: 0,
    avatar: 'http://prikachi.com/images/569/9566569j.png',
    level: 1,
    games: 0,
    wins: 0,
    streak: 0,
    rang_position: 1
  },
  token: '10200a9107a7fa87ae30eae506c6c728764f3b2f'
}
```

### GET /api/accounts/logout/
Не приема или връща нищо.

### /api/games/
data: ```json
{ username: "nsekulov" }
```
response: ```
{
  id: 2,
  channel: '1b92849f-4fd3-44b1-94a0-f51ee4026fcd',
  players: [
    {
      id: 1,
      avatar: 'http://prikachi.com/images/569/9566569j.png',
      username: 'vkolova'
    }
  ],
  state: 'initial',
  created: '2022-07-16T12:48:13.196704Z',
  finished: null,
  winner: null,
  rounds: [],
  data: null
}
```
/api/games/<id>/
params:
response:
/api/player/<id>/
params:
response:
/api/players/
params:
response:




Socket:
`ws://localhost:8001/ws/game/${user.token}/${game.uuid}/`;

