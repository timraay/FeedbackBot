# FeedbackBot: Gathering feedback in an effective, clean and simple manner.

<img align="right" width="260" height="260" src="images/icon.png">

FeedbackBot is a Discord bot made by timraay/Abusify that allows you to streamline the process of creating and gathering feedback on a large scale.

Invite it to your server by [clicking here](https://discord.com/api/oauth2/authorize?client_id=811927151631794236&permissions=8&scope=bot)!

### License
FeedbackBot has a GNU GPLv3 license. In short, you can obtain a copy of the source code, modify it, and even distribute it. When modifying the code though, you must keep the GNU GPLv3 license. Your software should also be marked as changed, with a reference to the original source code.

# Preview
<div style="text-align:center">
With FeedbackBot you will be able to easily create feedback, whilst still making it look nice and clean. Embeds are used for that organized look, while users can still attach images and other files just fine.

<img src="images/feedback.png">

Users will get a private channel when creating feedback. In here they will be asked to write their feedback, possibly select a label, and then confirm that the final result looks okay. Creating feedback can be canceled at any time by both the user and moderators.

<img src="images/selectlabel.png">
<img src="images/createfeedback.png">

Everything is customizable. Not only for members of your server, but also for admins it is easy to manage with clear and user-friendly commands and other actions.

<i>
<img src="images/setupfeed.png">

Setting up a feed

<img src="images/delete.png">

Deleting the feed
</i></div>

# Docs

FeedbackBot operates on a **guild**-wide basis. In case you didn't know, a guild is the official term for a Discord server. As an admin, you can create **feeds** for this guild. A feed is nothing more than a channel that members of your guild can submit feedback to.

For each feed, you can (but don't have to) create **labels**. Members can assign a pre-defined label to their feedback to further categorize it.

And finally we have **triggers**. Triggers are reactions under a message which members may react with to start creating feedback for the feed it is bound to. This too is completely optional, but it is a lot cleaner than running a command.

Now that you understand the basic terms, we can move on. Using the command `f!help [topic]` you can read more about specifics and how to set them up. Available topics are feeds, labels, triggers, feedback, permissions.

## Feeds

A feed consists of 5 elements: The name, shortname, color, description, and channel.

The name is displayed above all feedback. The shortname is used to reference your feed in commands. It should be a simplified version of your feed's name. The color of the feed translates to the colored bar on the left side of this message. The feed's channel is where all feedback will be sent to. Additionally, there's an option to make feedback in this feed anonymous.

Feeds can be accessed using one main command, `f!feed`! Alternatively, you can also use its plural `f!feeds`.

### Creating a feed

Creating a feed is simple. You run the command `f!feed create`. This will initiate the creation process. Here it will ask you step by step for all above mentioned elements. Follow the instructions it gives you. Once you finish, you can now view your feed using the `f!feed <feed>` command. Creating a feed requires admin permissions.

### Customizing a feed

The below commands can be used to show or modify properties of an already existing feed.
```
f!feed <feed> name [new_value..]
f!feed <feed> shortname [new_value..]
f!feed <feed> desc [new_value..]
f!feed <feed> color [new_value]
f!feed <feed> channel [new_value..]
f!feed <feed> anonymous [new_value]
```
To delete a feed, use `f!feed <feed> delete`.

## Labels

Labels are a way of further categorizing feedback. Just like feeds, labels have a name, shortname, color, description, but also an emoji. The label's color will overwrite the feed's color, whereas the label's name and description are displayed alongside the feed's. The emoji is used in the feedback creation process to select a label.

Since labels are an extension of feeds, you can access them using the command `f!feed <feed> labels`. Using `label` instead of `labels` will also work.

### Creating a label

Creating a label is similar to creating a feed. Run the command `f!feed <feed> label create` and follow the instructions. Once you finish, you can now view your label using the `f!feed <feed> label <label>` command. Creating a label requires admin permissions.

### Customizing a label

The below commands can be used to show or modify properties of an existing label.
```
f!feed <feed> label <label> name [new_value..]
f!feed <feed> label <label> shortname [new_value..]
f!feed <feed> label <label> desc [new_value..]
f!feed <feed> label <label> color [new_value]
f!feed <feed> label <label> emoji [new_value]
```
To delete a label, use `f!feed <feed> label <label> delete`.

## Triggers

Triggers are a more fancy way of letting users create feedback. Instead of having to run a command, users can react to a message. A trigger consists of 3 elements: An emoji, a message users can react to with the given emoji, and a feed to create feedback for once triggered.

While each trigger is specific to a single feed, they are treated as standalone objects, unlike labels. For that reason they have their own command, `f!triggers` (or `f!trigger`, additionally). Creating a trigger requires admin permissions.

### Creating a trigger

Even for triggers, there is a creation process. Run the command `f!trigger create` and follow the instructions. Once you finish, you can view your trigger using the `f!trigger <trigger>` command. Since triggers have no shortname, you have to select them by index.

### Customizing a trigger

The below commands can be used to show or modify properties of an existing trigger.
```
f!triggers <trigger> feed [value]
f!triggers <trigger> emoji [value]
f!triggers <trigger> message [value]
```
To delete a trigger, use `f!trigger <trigger> delete`.

### Feedback

What feedback is and how to create it is all what your guild members will have to know, and it is your job to tell them. Using feed and label descriptions is a great way of giving the user some guidelines as to what to write, too.

### Creating feedback

Feedback can be created in two ways. Users can run the `f!new <feed>` command, or trigger a trigger. When triggered, a private channel is created in the same channel category the feed is in. If there are labels available, it will first prompt you to choose one. Once that's done, you can write your actual feedback in a single message, additionally including an attachment. Finally, it will show you what your feedback will look like and ask you to confirm before sending it. If you decline, you can type your message again. When the feedback is done the channel will be removed again.

### Viewing feedback

Feedback is sent to the feed's channel. Anyone with access to that channel can thus see the feedback message. Moderators however can also see a more detailed look of the feedback elsewhere using the `f!feedback <feed> <feedback>`, "feed" being the shortname or index of the feed and "feedback" being the ID each feedback gets (the number after the hashtag). Currently it is not possible to edit feedback. Alternatively, moderators can list all feedback sent by a specific user using the command `f!fb user <user>`.

### Deleting feedback

Just like creating it, feedback can be deleted in two ways. You can use the command, `f!fb <feed> <feedback> delete`, or simply delete the feedback message. When feedback is being created, both the creator and moderators can cancel it by typing "cancel" at the right time.

## Permissions & Moderation

By default, the only thing members can do is create feedback. Though, there's two different types of permissions you can assign to a role, to then grant to specific users.

The first permission level is moderator. This will give users access to view feedback, view feedback creation channels, and delete them. They can also export feedback using the `f!export [(csv|json)]` command.

The second permission level is administrator. This includes all the permissions a moderator has, as well as the ability to create, modify and delete feeds, labels and triggers. Admins can also change the roles these permissions are assigned to, as well as the bot's prefix, using `f!config`.

Note that if a member of your server has Discord's administrator permission, the bot will also give the user admin perms, even if the user doesn't have the so-called admin role.

### Setting up a role with permissions

Permissions are part of the guild's config, see `f!config`. You can assign a role to have mod or admin permissions with the `f!cf (mod|admin) <role>` command. Changes are applied immediately.

## All commands
```
f!help [topic]
f!new <feed>

f!feeds
f!feeds create
f!feeds <feed>
f!feeds <feed> delete
f!feeds <feed> name [new_value..]
f!feeds <feed> shortname [new_value..]
f!feeds <feed> desc [new_value..]
f!feeds <feed> color [new_value]
f!feeds <feed> channel [new_value..]
f!feeds <feed> anonymous [new_value]
f!feeds <feed> labels
f!feeds <feed> labels create
f!feeds <feed> labels <label>
f!feeds <feed> labels <label> delete
f!feeds <feed> labels <label> name [new_value..]
f!feeds <feed> labels <label> shortname [new_value..]
f!feeds <feed> labels <label> desc [new_value..]
f!feeds <feed> labels <label> color [new_value]
f!feeds <feed> labels <label> emoji [new_value]

f!triggers
f!triggers create
f!triggers <trigger>
f!triggers <trigger> delete
f!triggers <trigger> feed <value>
f!triggers <trigger> emoji <value>
f!triggers <trigger> message <value>

f!feedback <feed_id> <feedback_id>
f!export (csv|json)

f!config [option] [value]

f!invite
f!ping
```