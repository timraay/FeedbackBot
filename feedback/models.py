import sqlite3
db = sqlite3.connect('feedback.db')
cur = db.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS "feedback" (
	"feed_id"	INTEGER,
	"label_id"	INTEGER,
	"feedback_id"	INTEGER,
	"feedback_author"	INTEGER,
	"feedback_desc"	TEXT,
	"feedback_desc_url"	TEXT,
	"finished"	INTEGER,
	"channel_id"	INTEGER,
	"message_id"	INTEGER,
	"creation_channel_id"	INTEGER
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS "feeds" (
	"guild_id"	INTEGER,
	"feed_id"	INTEGER,
	"feed_name"	TEXT,
	"feed_shortname"	TEXT,
	"feed_color"	TEXT,
	"feed_desc"	TEXT,
	"feed_desc_url"	TEXT,
	"feed_channel_id"	INTEGER,
	"anonymous"	INTEGER DEFAULT 0,
	"reactions"	TEXT,
	PRIMARY KEY("feed_id")
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS "guilds" (
	"guild_id"	INTEGER,
	"command_prefix"	TEXT DEFAULT 'f!',
	"admin_role"	INTEGER DEFAULT 0,
	"mod_role"	INTEGER DEFAULT 0,
	PRIMARY KEY("guild_id")
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS "labels" (
	"feed_id"	INTEGER,
	"label_id"	INTEGER,
	"label_name"	TEXT,
	"label_shortname"	TEXT,
	"label_color"	TEXT,
	"label_desc"	TEXT,
	"label_desc_url"	TEXT,
	"label_emoji"	TEXT,
	PRIMARY KEY("label_id")
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS "triggers" (
	"guild_id"	INTEGER,
	"feed_id"	INTEGER,
	"trigger_id"	INTEGER,
	"trigger_emoji"	TEXT,
	"trigger_channel_id"	INTEGER,
	"trigger_message_id"	INTEGER,
	PRIMARY KEY("trigger_id")
)""")
db.commit()

from discord.ext.commands import has_role, has_any_role, check, CheckFailure

class Guild():
    def __init__(self, guild_id):
        cur.execute("SELECT * FROM guilds WHERE guild_id = ?", (guild_id,))
        res = cur.fetchone()
        if not res: raise NotFound('Guild %s is not in database' % guild_id)
        self.guild_id, self.command_prefix, self.admin_role, self.mod_role = res

    @classmethod
    def create(cls, guild_id, command_prefix='f!', admin_role=0, mod_role=0):
        cur.execute("INSERT INTO guilds VALUES (?,?,?,?)", (guild_id, command_prefix, admin_role, mod_role))
        db.commit()
        return cls(guild_id)

    def save(self):
        cur.execute("UPDATE guilds SET command_prefix = ?, admin_role = ?, mod_role = ? WHERE guild_id = ?", (self.command_prefix, self.admin_role, self.mod_role, self.guild_id))
        db.commit()

    @property
    def feeds(self):
        cur.execute('SELECT feed_id FROM feeds WHERE guild_id = ? ORDER BY feed_id', (self.guild_id,))
        return [Feed('feed_id', feed_id[0]) for feed_id in cur.fetchall()]
    @property
    def feedback(self):
        feedback = list()
        for feed in self.feeds:
            feedback += feed.feedback
        return feedback
    @property
    def triggers(self):
        cur.execute('SELECT trigger_id FROM triggers WHERE guild_id = ? ORDER BY trigger_id', (self.guild_id,))
        return [Trigger('trigger_id', trigger_id[0]) for trigger_id in cur.fetchall()]
def has_perms(level=2):
    async def predicate(ctx):
        guild = Guild(ctx.guild.id)
        perms = ctx.channel.permissions_for(ctx.author)
        try:
            if perms.administrator: return True
            elif level == 1: return await has_any_role(guild.admin_role, guild.mod_role).predicate(ctx)
            elif level == 2: return await has_role(guild.admin_role).predicate(ctx)
        except CheckFailure:
            return False
    return check(predicate)

class Feed():
    def __init__(self, key, value):
        cur.execute(f"SELECT * FROM feeds WHERE {key} = ?", (value,))
        res = cur.fetchone()
        if not res: raise NotFound('Feed %s does not match %s' % (key, value))
        (self.guild_id, self.feed_id, self.feed_name, self.feed_shortname, self.feed_color,
        self.feed_desc, self.feed_desc_url, self.feed_channel_id, self.anonymous, self.reactions) = res

    @classmethod
    def create(cls, guild_id, feed_name, feed_shortname, feed_color, feed_desc, feed_desc_url, feed_channel_id, anonymous=0, reactions=""):
        cur.execute("SELECT MAX(feed_id) FROM feeds")
        old_id = cur.fetchone()[0]
        feed_id = old_id+1 if old_id else 1
        cur.execute("INSERT INTO feeds VALUES (?,?,?,?,?,?,?,?,?,?)", (int(guild_id), int(feed_id), str(feed_name), str(feed_shortname), str(feed_color), str(feed_desc), str(feed_desc_url), int(feed_channel_id), int(anonymous), str(reactions)))
        db.commit()
        return cls('feed_id', feed_id)
    
    @classmethod
    def find(cls, guild_id, feed_shortname):
        try: index = int(feed_shortname)
        except ValueError:
            cur.execute(f"SELECT feed_id FROM feeds WHERE guild_id = ? AND feed_shortname = ?", (guild_id, feed_shortname))
            feed_id = cur.fetchone()
            if not feed_id: raise NotFound('No feed could be found with shortname %s' % feed_shortname)
        else:
            cur.execute(f"SELECT feed_id FROM feeds WHERE guild_id = ? ORDER BY feed_id LIMIT ?,1", (guild_id, index-1))
            feed_id = cur.fetchone()
            if not feed_id: raise NotFound('No feed could be found with index %s' % index)
        return cls('feed_id', feed_id[0])

    def save(self):
        cur.execute("""UPDATE feeds SET
        guild_id = ?, feed_name = ?, feed_shortname = ?, feed_color = ?, feed_desc = ?,
        feed_desc_url = ?, feed_channel_id = ?, anonymous = ?, reactions = ? WHERE feed_id = ?""",
        (self.guild_id, self.feed_name, self.feed_shortname, self.feed_color, self.feed_desc,
        self.feed_desc_url, self.feed_channel_id, self.anonymous, self.reactions, self.feed_id))
        db.commit()
    
    def delete(self):
        cur.execute("DELETE FROM feeds WHERE feed_id = ?", (self.feed_id,))
        cur.execute("DELETE FROM labels WHERE feed_id = ?", (self.feed_id,))
        cur.execute("DELETE FROM feedback WHERE feed_id = ?", (self.feed_id,))
        cur.execute("DELETE FROM triggers WHERE feed_id = ?", (self.feed_id,))
        db.commit()
        self = None

    @property
    def guild(self):
        return Guild(self.guild_id)
    @property
    def labels(self):
        cur.execute('SELECT label_id FROM labels WHERE feed_id = ? ORDER BY label_id', (self.feed_id,))
        return [Label('label_id', label_id[0]) for label_id in cur.fetchall()]
    @property
    def feedback(self):
        cur.execute('SELECT feedback_id FROM feedback WHERE feed_id = ? AND finished = 1', (self.feed_id,))
        return [Feedback(self.feed_id, 'feedback_id', feedback_id[0]) for feedback_id in cur.fetchall()]
    @property
    def triggers(self):
        cur.execute('SELECT trigger_id FROM triggers WHERE feed_id = ? ORDER BY trigger_id', (self.feed_id,))
        return [Trigger('trigger_id', trigger_id[0]) for trigger_id in cur.fetchall()]
    @property
    def index(self):
        cur.execute("SELECT feed_id FROM feeds WHERE guild_id = ? ORDER BY feed_id", (self.guild_id,))
        for i, (feed_id,) in enumerate(cur.fetchall()):
            if feed_id == self.feed_id:
                return i
        raise NotFound('Index of feed %s could not be found with guild_id %s' % (self.feed_shortname, self.guild_id))

    def get_label(self, label_shortname):
        cur.execute("SELECT label_id FROM labels WHERE feed_id = ? AND label_shortname", (self.feed_id, label_shortname))
        label_id = cur.fetchone()
        if not label_id: raise NotFound('No label could be found with shortname %s' % label_shortname)
        return Label('label_id', label_id[0])

class Label():
    def __init__(self, key, value):
        cur.execute(f"SELECT * FROM labels WHERE {key} = ?", (value,))
        res = cur.fetchone()
        if not res: raise NotFound('Label %s does not match %s' % (key, value))
        (self.feed_id, self.label_id, self.label_name, self.label_shortname, self.label_color, self.label_desc, self.label_desc_url, self.label_emoji) = res

    @classmethod
    def create(cls, feed_id, label_name, label_shortname, label_color, label_desc, label_desc_url, label_emoji):
        cur.execute("SELECT MAX(label_id) FROM labels")
        old_id = cur.fetchone()[0]
        label_id = old_id+1 if old_id else 1
        cur.execute("INSERT INTO labels VALUES (?,?,?,?,?,?,?,?)", (int(feed_id), int(label_id), str(label_name), str(label_shortname), str(label_color), str(label_desc), str(label_desc_url), str(label_emoji)))
        db.commit()
        return cls('label_id', label_id)
    
    @classmethod
    def find(cls, feed, label_shortname):
        try: index = int(label_shortname)
        except ValueError:
            cur.execute(f"SELECT label_id FROM labels WHERE feed_id = ? AND label_shortname = ?", (feed.feed_id, label_shortname))
            label_id = cur.fetchone()
            if not label_id: raise NotFound('No label could be found with shortname %s' % label_shortname)
        else:
            cur.execute(f"SELECT label_id FROM labels WHERE feed_id = ? ORDER BY label_id LIMIT ?,1", (feed.feed_id, index-1))
            label_id = cur.fetchone()
            if not label_id: raise NotFound('No label could be found with index %s' % index)
        return cls('label_id', label_id[0])

    @property
    def feed(self):
        return Feed('feed_id', self.feed_id)
    @property
    def index(self):
        cur.execute("SELECT label_id FROM labels WHERE feed_id = ? ORDER BY label_id", (self.feed_id,))
        for i, (label_id) in enumerate(cur.fetchall()):
            if label_id == self.label_id:
                return i
        raise NotFound('Label %s could not be found with feed_id %s' % (self.label_shortname, self.feed_id))

    def save(self):
        cur.execute("""UPDATE labels SET
        feed_id = ?, label_name = ?, label_shortname = ?, label_color = ?, label_desc = ?, label_desc_url = ?, label_emoji = ? WHERE label_id = ?""",
        (self.feed_id, self.label_name, self.label_shortname, self.label_color, self.label_desc, self.label_desc_url, self.label_emoji, self.label_id))
        db.commit()

    def delete(self):
        cur.execute("DELETE FROM labels WHERE label_id = ?", (self.label_id,))
        cur.execute("UPDATE feedback SET label_id = ? WHERE label_id = ?", (0, self.label_id))
        db.commit()
        self = None

class Feedback():
    def __init__(self, feed_id, key, value):
        cur.execute(f"SELECT * FROM feedback WHERE feed_id = ? AND {key} = ?", (feed_id, value,))
        res = cur.fetchone()
        if not res: raise NotFound('Feedback %s does not match %s' % (key, value))
        (self.feed_id, self.label_id, self.feedback_id, self.feedback_author, self.feedback_desc,
        self.feedback_desc_url, self.finished, self.channel_id, self.message_id, self.creation_channel_id) = res

    @classmethod
    def create(cls, feed_id, label_id, feedback_author, feedback_desc, feedback_desc_url='', finished=1, channel_id=0, message_id=0, creation_channel_id=0):
        cur.execute("SELECT MAX(feedback_id) FROM feedback WHERE feed_id = ?", (feed_id,))
        old_id = cur.fetchone()[0]
        feedback_id = old_id+1 if old_id else 1
        cur.execute("INSERT INTO feedback VALUES (?,?,?,?,?,?,?,?,?,?)", (int(feed_id), int(label_id), int(feedback_id), int(feedback_author), str(feedback_desc), str(feedback_desc_url), int(finished), int(channel_id), int(message_id), int(creation_channel_id)))
        db.commit()
        return cls(feed_id, 'feedback_id', feedback_id)
    
    @classmethod
    def new(cls, feed_id, feedback_author, creation_channel_id, label_id=None, feedback_desc=None, feedback_desc_url=None, finished=0, channel_id=None, message_id=None):
        cur.execute("SELECT MAX(feedback_id) FROM feedback WHERE feed_id = ?", (feed_id,))
        old_id = cur.fetchone()[0]
        feedback_id = old_id+1 if old_id else 1
        cur.execute("INSERT INTO feedback VALUES (?,?,?,?,?,?,?,?,?,?)", (feed_id, label_id, feedback_id, feedback_author, feedback_desc, feedback_desc_url, int(finished), channel_id, message_id, int(creation_channel_id)))
        db.commit()
        return cls(feed_id, 'feedback_id', feedback_id)

    @classmethod
    def find(cls, channel_id, message_id):
        cur.execute("SELECT feed_id, feedback_id FROM feedback WHERE channel_id = ? and message_id = ?", (channel_id, message_id))
        res = cur.fetchone()
        if res: return cls(res[0], 'feedback_id', res[1])
        else: raise NotFound('Feedback not found with message %s-%s' % (channel_id, message_id))

    def save(self):
        cur.execute("""UPDATE feedback SET
        label_id = ?, feedback_author = ?, feedback_desc = ?, feedback_desc_url = ?, finished = ?,
        channel_id = ?, message_id = ?, creation_channel_id = ? WHERE feed_id = ? AND feedback_id = ?""",
        (self.label_id, self.feedback_author, self.feedback_desc, self.feedback_desc_url, self.finished,
        self.channel_id, self.message_id, self.creation_channel_id, self.feed_id, self.feedback_id))
        db.commit()

    @property
    def label(self):
        return Label('label_id', self.label_id) if self.label_id else None
    @property
    def feed(self):
        return Feed('feed_id', self.feed_id)

    def delete(self):
        cur.execute("DELETE FROM feedback WHERE feed_id = ? AND feedback_id = ?", (self.feed_id, self.feedback_id))
        db.commit()
        self = None
def has_unfinished_feedback(guild_id, user_id):
    cur.execute("""SELECT feed_id, feedback_id FROM feedback
    WHERE feed_id IN (SELECT feed_id FROM feeds WHERE guild_id = ?)
    AND feedback_author = ? AND finished = 0""", (guild_id, user_id))
    res = cur.fetchone()
    if res: return Feedback(res[0], 'feedback_id', res[1])
    else: return None
def get_feedback_by_user_id(user_id):
    cur.execute("SELECT feed_id, feedback_id FROM feedback WHERE feedback_author = ? AND finished = 1", (user_id,))
    return [Feedback(feed_id, 'feedback_id', feedback_id) for feed_id, feedback_id in cur.fetchall()]

class Trigger():
    def __init__(self, key, value):
        cur.execute(f"SELECT * FROM triggers WHERE {key} = ?", (value,))
        res = cur.fetchone()
        if not res: raise NotFound('Trigger %s does not match %s' % (key, value))
        (self.guild_id, self.feed_id, self.trigger_id, self.trigger_emoji, self.trigger_channel_id, self.trigger_message_id) = res

    @classmethod
    def create(cls, guild_id, feed_id, trigger_emoji, trigger_channel_id, trigger_message_id):
        cur.execute("SELECT MAX(trigger_id) FROM triggers")
        old_id = cur.fetchone()[0]
        trigger_id = old_id+1 if old_id else 1
        cur.execute("INSERT INTO triggers VALUES (?,?,?,?,?,?)", (int(guild_id), int(feed_id), int(trigger_id), str(trigger_emoji), int(trigger_channel_id), int(trigger_message_id)))
        db.commit()
        return cls('trigger_id', trigger_id)
    
    @classmethod
    def find(cls, guild_id, index):
        cur.execute(f"SELECT trigger_id FROM triggers WHERE guild_id = ? ORDER BY trigger_id LIMIT ?,1", (guild_id, int(index)-1))
        trigger_id = cur.fetchone()
        if not trigger_id: raise NotFound('No trigger could be found with index %s' % index)
        return cls('trigger_id', trigger_id[0])
    
    @classmethod
    def match(cls, message_id, trigger_emoji):
        cur.execute(f"SELECT trigger_id FROM triggers WHERE trigger_message_id = ? AND trigger_emoji = ? ORDER BY trigger_id", (message_id, trigger_emoji))
        trigger_id = cur.fetchone()
        if not trigger_id: raise NotFound('No trigger could be found with trigger_message_id %s and trigger_emoji %s' % (message_id, trigger_emoji))
        return cls('trigger_id', trigger_id[0])

    @property
    def feed(self):
        return Feed('feed_id', self.feed_id)
    @property
    def guild(self):
        return Guild(self.guild_id)
    @property
    def index(self):
        cur.execute("SELECT trigger_id FROM triggers WHERE guild_id = ? ORDER BY trigger_id", (self.guild_id,))
        for i, (trigger_id,) in enumerate(cur.fetchall()):
            if trigger_id == self.trigger_id:
                return i
        raise NotFound('Trigger could not be found with trigger_id %s' % self.trigger_id)

    def save(self):
        cur.execute("""UPDATE triggers SET
        guild_id = ?, feed_id = ?, trigger_emoji = ?, trigger_channel_id = ?, trigger_message_id = ? WHERE trigger_id = ?""",
        (self.guild_id, self.feed_id, self.trigger_emoji, self.trigger_channel_id, self.trigger_message_id, self.trigger_id))
        db.commit()

    def delete(self):
        cur.execute("DELETE FROM triggers WHERE trigger_id = ?", (self.trigger_id,))
        db.commit()
        self = None


class NotFound(Exception):
    """Raised when a database row couldn't be found"""
    pass
