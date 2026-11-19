from pydantic import BaseModel, ValidationError

from app.domains.llm.schemas import ToolSpec


class ToolExecutionError(Exception):
    """Un outil n'a pas pu s'exécuter. Le message est renvoyé au modèle, qui peut s'adapter."""


class Tool:
    """Un outil de l'agent : un nom, une description, des arguments typés et une action.

    Le modèle ne lance jamais rien lui-même : il *demande* un outil avec des arguments, et c'est
    notre code qui valide ces arguments puis exécute. `sensitive` marque les actions qui ont un
    effet de bord important : elles exigent l'approbation d'un humain.
    """

    name: str
    description: str
    args_model: type[BaseModel]
    sensitive: bool = False

    def spec(self) -> ToolSpec:
        return ToolSpec(self.name, self.description, self.args_model.model_json_schema())

    def run(self, arguments) -> str:
        raise NotImplementedError


class ToolRegistry:
    """Les outils disponibles, avec validation des arguments avant toute exécution."""

    def __init__(self, tools: list[Tool]):
        self._tools = {tool.name: tool for tool in tools}

    def specs(self) -> list[ToolSpec]:
        return [tool.spec() for tool in self._tools.values()]

    def is_sensitive(self, name: str) -> bool:
        return self._tool(name).sensitive

    def validate(self, name: str, raw_arguments: dict) -> BaseModel:
        """Valide les arguments reçus du modèle ; toute erreur est expliquée au modèle."""
        tool = self._tool(name)
        unexpected = set(raw_arguments) - set(tool.args_model.model_fields)
        if unexpected:
            raise ToolExecutionError(
                f"Arguments non prévus pour {name} : {', '.join(sorted(unexpected))}"
            )
        try:
            return tool.args_model.model_validate(raw_arguments)
        except ValidationError as error:
            details = "; ".join(
                f"{'.'.join(str(part) for part in issue['loc'])} : {issue['msg']}"
                for issue in error.errors()
            )
            raise ToolExecutionError(f"Arguments invalides pour {name} : {details}") from error

    def execute(self, name: str, raw_arguments: dict) -> str:
        return self._tool(name).run(self.validate(name, raw_arguments))

    def _tool(self, name: str) -> Tool:
        if name not in self._tools:
            raise ToolExecutionError(f"Outil inconnu : {name}")
        return self._tools[name]
