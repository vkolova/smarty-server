## Аутентикация


### POST /api/accounts/register/
Приема

```javascript
{
    username: "vkolova",
    password: "..."
}
```

връща
```javascript
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

```javascript
{
    username: "vkolova",
    password: "..."
}
```

връща
```javascript
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
Не приема или връща нищо. (Authorization token се подава!)


## Игри и играчи

### POST /api/games/
Създава игра и праща покана за игра на друг играч (задължително!).
data:
```javascript
{ username: "nsekulov" }
```

response:
```javascript
{
  id: 2,
  channel: '1b92849f-4fd3-44b1-94a0-f51ee4026fcd', // ID на играта!
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


### GET /api/games/<id>/
Връща информация за дадената игра.

### GET /api/players/me/
Връща информация за текущия играч.


### GET /api/player/<id>/
Връща информация за играч с `id`.

### GET  /api/players/
Връща топ 10 играчи, базирано на натрупани точки.



## Web socket-и

### За идващи покиани:
`ws://localhost:8001/ws/invitations/${user.token}/`;

### По време на игра:
`ws://localhost:8001/ws/game/${user.token}/${game.uuid}/`;


```
> `game_connect` - съобщавате, че сте готови играта да започне


> `game_update` - получавате ъпдейт за състоянието на играта; 
> `scores_update` - получавате ъпдейт на точките
> `round_winner` - съобщава победителя в рунда
> `question_update` - получавате нов въпрос

> `question_answer` - изпращате отговор
{
    type: 'question_answer',
    data: {
        'answer': <answer_id>,
        'time': <remaining_time_in_seconds>
    }
}
```